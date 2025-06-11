from player import Player
from database import Database
import random
import json
from datetime import datetime, timedelta

class FarmingSystem:
    def __init__(self):
        self.db = Database()
        self.load_plants()
        
    def load_plants(self):
        """加载所有灵植数据"""
        self.plants = {}
        plants_data = self.db.fetch_all("SELECT * FROM plants")
        for plant in plants_data:
            self.plants[plant[0]] = {
                'name': plant[1],
                'growth_stages': plant[2],
                'required_environment': plant[3],
                'yield_items': json.loads(plant[4]),
                'variant_chance': plant[5]
            }
        
    def list_plants(self) -> str:
        """列出所有可种植灵植"""
        if not self.plants:
            return "当前没有可种植的灵植"
            
        result = "可种植灵植:\n"
        for plant_id, plant in self.plants.items():
            result += f"{plant['name']} - 生长阶段: {plant['growth_stages']}\n"
            result += f"环境需求: {plant['required_environment']}\n"
            result += f"收获: {', '.join([f'{k}x{v}' for k, v in plant['yield_items'].items()])}\n"
            result += f"变异几率: {plant['variant_chance']*100}%\n\n"
            
        return result
        
    def plant_seed(self, player: Player, plant_name: str, plot_id: int = 1) -> str:
        """种植灵植"""
        # 查找灵植
        plant = None
        plant_id = None
        # 首先通过名称查找植物ID
        for pid, p in self.plants.items():
            if p['name'] == plant_name:
                plant = p
                plant_id = pid
                break
                
        if not plant:
            return f"未知灵植: {plant_name}"
            
        # 检查种子
        seed_id = f"{plant_name}种子"
        if player.items.get(seed_id, {}).get('count', 0) < 1:
            return f"你需要{seed_id}才能种植"
            
        # 检查地块是否空闲
        existing_plant = self.db.fetch_one(
            "SELECT plant_id FROM player_farms WHERE qq_id = ? AND plot_id = ?",
            (player.qq_id, plot_id)
        )
        if existing_plant:
            return f"地块{plot_id}已经被占用"
            
        # 开始种植
        player.remove_item(seed_id, 1)
        growth_time = datetime.now() + timedelta(hours=plant['growth_stages'])
        
        # 使用找到的plant_id而不是plant['id']
        self.db.execute(
            """INSERT INTO player_farms 
            (qq_id, plot_id, plant_id, growth_stage, growth_time)
            VALUES (?, ?, ?, 1, ?)""",
            (player.qq_id, plot_id, plant_id, growth_time.strftime("%Y-%m-%d %H:%M:%S"))
        )
        
        return f"你成功在地块{plot_id}种植了{plant_name}，预计{plant['growth_stages']}小时后成熟。"
        
    def check_plants(self, player: Player) -> str:
        """检查玩家的灵植状态"""
        plants_data = self.db.fetch_all(
            "SELECT plot_id, plant_id, growth_stage, growth_time, is_variant FROM player_farms WHERE qq_id = ?",
            (player.qq_id,)
        )
        
        if not plants_data:
            return "你当前没有种植任何灵植"
            
        result = "你的灵植状态:\n"
        current_time = datetime.now()
        
        for plot_id, plant_id, growth_stage, growth_time, is_variant in plants_data:
            plant = self.plants.get(plant_id, {})
            grow_time = datetime.strptime(growth_time, "%Y-%m-%d %H:%M:%S")
            
            if current_time >= grow_time:
                # 可以收获
                result += f"地块{plot_id}: {plant.get('name', '未知灵植')} 已成熟！\n"
                if is_variant:
                    result += " (变异植株) "
            else:
                # 还在生长
                remaining = grow_time - current_time
                hours = remaining.seconds // 3600
                minutes = (remaining.seconds // 60) % 60
                result += f"地块{plot_id}: {plant.get('name', '未知灵植')} 生长中 ({growth_stage}/{plant.get('growth_stages', 1)}阶段) "
                result += f"剩余时间: {hours}小时{minutes}分钟\n"
                
        return result
        
    def harvest_plant(self, player: Player, plot_id: int) -> str:
        """收获灵植"""
        plant_data = self.db.fetch_one(
            "SELECT plant_id, growth_stage, is_variant FROM player_farms WHERE qq_id = ? AND plot_id = ?",
            (player.qq_id, plot_id)
        )
        
        if not plant_data:
            return f"地块{plot_id}没有可收获的灵植"
            
        plant_id, growth_stage, is_variant = plant_data
        plant = self.plants.get(plant_id)
        
        if not plant:
            # 清理无效数据
            self.db.execute(
                "DELETE FROM player_farms WHERE qq_id = ? AND plot_id = ?",
                (player.qq_id, plot_id)
            )
            return f"地块{plot_id}的灵植数据异常，已自动清理"
            
        # 检查是否成熟
        growth_data = self.db.fetch_one(
            "SELECT growth_time FROM player_farms WHERE qq_id = ? AND plot_id = ?",
            (player.qq_id, plot_id)
        )
        if not growth_data:
            return "数据错误，请稍后再试"
            
        grow_time = datetime.strptime(growth_data[0], "%Y-%m-%d %H:%M:%S")
        if datetime.now() < grow_time:
            return f"地块{plot_id}的灵植尚未成熟"
            
        # 收获物品
        yield_items = plant['yield_items']
        if is_variant:
            # 变异植株产量翻倍
            yield_items = {k: v * 2 for k, v in yield_items.items()}
            
        for item, count in yield_items.items():
            player.add_item(item, count)
            
        # 有几率获得种子
        if random.random() < 0.7:  # 70%几率获得种子
            seed_id = f"{plant['name']}种子"
            player.add_item(seed_id, 1)
            
        # 木灵根加成
        if '木' in player.roots and random.random() < 0.3:
            extra_item = random.choice(list(yield_items.keys()))
            player.add_item(extra_item, 1)
            bonus_msg = "\n木灵根触发植物亲和，额外获得一份收获！"
        else:
            bonus_msg = ""
            
        # 移除种植记录
        self.db.execute(
            "DELETE FROM player_farms WHERE qq_id = ? AND plot_id = ?",
            (player.qq_id, plot_id)
        )
        
        # 种植技能经验
        player.add_skill_exp('种植术', 5 + growth_stage)
        
        result = f"你从地块{plot_id}收获了{plant['name']}，获得: "
        result += ", ".join([f"{k}x{v}" for k, v in yield_items.items()])
        result += bonus_msg
        
        return result
        
    def accelerate_growth(self, player: Player, plot_id: int, item_id: str) -> str:
        """加速灵植生长"""
        # 检查地块
        plant_data = self.db.fetch_one(
            "SELECT plant_id, growth_time FROM player_farms WHERE qq_id = ? AND plot_id = ?",
            (player.qq_id, plot_id)
        )
        
        if not plant_data:
            return f"地块{plot_id}没有正在生长的灵植"
            
        plant_id, growth_time = plant_data
        grow_time = datetime.strptime(growth_time, "%Y-%m-%d %H:%M:%S")
        
        # 检查加速物品
        if item_id == '灵水':
            hours_reduced = 2
            item_cost = 1
        elif item_id == '生长符':
            hours_reduced = 8
            item_cost = 1
        else:
            return "无效的加速物品"
            
        if player.items.get(item_id, {}).get('count', 0) < item_cost:
            return f"你需要{item_id}x{item_cost}来加速生长"
            
        # 应用加速
        new_grow_time = grow_time - timedelta(hours=hours_reduced)
        player.remove_item(item_id, item_cost)
        
        self.db.execute(
            "UPDATE player_farms SET growth_time = ? WHERE qq_id = ? AND plot_id = ?",
            (new_grow_time.strftime("%Y-%m-%d %H:%M:%S"), player.qq_id, plot_id)
        )
        
        # 木灵根额外效果
        if '木' in player.roots and random.random() < 0.2:
            extra_reduce = 1
            new_grow_time = new_grow_time - timedelta(hours=extra_reduce)
            self.db.execute(
                "UPDATE player_farms SET growth_time = ? WHERE qq_id = ? AND plot_id = ?",
                (new_grow_time.strftime("%Y-%m-%d %H:%M:%S"), player.qq_id, plot_id)
            )
            bonus_msg = f"\n木灵根触发自然亲和，额外加速{extra_reduce}小时！"
        else:
            bonus_msg = ""
            
        return f"你使用{item_id}使地块{plot_id}的灵植生长加速了{hours_reduced}小时。{bonus_msg}"