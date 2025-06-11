from player import Player
from database import Database
import random
import json
from datetime import datetime, timedelta

class ForgingSystem:
    def __init__(self):
        self.db = Database()
        
    def get_learned_recipes(self, player: Player) -> list:
        """获取玩家已学习的炼器配方"""
        recipes = self.db.fetch_all(
            """SELECT f.name, f.type, f.grade, f.sub_grade, f.materials, f.attributes 
            FROM forging_recipes f
            JOIN player_recipes p ON f.recipe_id = p.recipe_id
            WHERE p.qq_id = ? AND p.recipe_type = 'forging'""",
            (player.qq_id,)
        )
        return recipes
        
    def list_recipes(self, player: Player) -> str:
        """列出玩家可用的炼器配方"""
        recipes = self.get_learned_recipes(player)
        
        if not recipes:
            return "你尚未学习任何炼器配方，请通过完成任务获取配方"
            
        result = "可炼制装备:\n"
        for name, item_type, grade, sub_grade, materials, attributes in recipes:
            materials = json.loads(materials)
            attributes = json.loads(attributes)
            result += f"{name} ({item_type}-{grade}{sub_grade})\n"
            result += "属性: " + ", ".join([f"{k}+{v}" for k, v in attributes.items()]) + "\n"
            result += "需要材料: " + ", ".join([f"{k}x{v}" for k, v in materials.items()])
            result += "\n\n"
            
        return result
        
    def learn_recipe(self, player: Player, recipe_name: str) -> bool:
        """学习炼器配方"""
        recipe = self.db.fetch_one(
            "SELECT recipe_id FROM forging_recipes WHERE name = ?",
            (recipe_name,)
        )
        if not recipe:
            return False
            
        # 检查是否已学习
        known = self.db.fetch_one(
            "SELECT 1 FROM player_recipes WHERE qq_id = ? AND recipe_id = ?",
            (player.qq_id, recipe[0])
        )
        if known:
            return True
            
        self.db.execute(
            "INSERT INTO player_recipes (qq_id, recipe_type, recipe_id) VALUES (?, 'forging', ?)",
            (player.qq_id, recipe[0])
        )
        return True
        
    def forge_item(self, player: Player, item_name: str) -> str:
        """炼制装备"""
        # 查找配方
        recipe = self.db.fetch_one(
            """SELECT f.recipe_id, f.materials, f.attributes 
            FROM forging_recipes f
            JOIN player_recipes p ON f.recipe_id = p.recipe_id
            WHERE p.qq_id = ? AND f.name = ?""",
            (player.qq_id, item_name)
        )
        if not recipe:
            return f"你尚未学习{item_name}的炼制方法"
            
        recipe_id, materials, attributes = recipe
        materials = json.loads(materials)
        
        # 检查材料
        for item, count in materials.items():
            if player.items.get(item, {}).get('count', 0) < count:
                return f"材料不足，需要{item}x{count}"
                
        # 计算成功率
        success_rate = self.calculate_success_rate(player, recipe_id)
        quality_rate = random.random()
        
        # 确定装备品质
        if quality_rate < 0.1:
            quality = "极品"
            attr_multiplier = 1.2
        elif quality_rate < 0.3:
            quality = "上"
            attr_multiplier = 1.1
        elif quality_rate < 0.6:
            quality = "中"
            attr_multiplier = 1.0
        else:
            quality = "下"
            attr_multiplier = 0.9
            
        success = random.random() < success_rate
        
        # 消耗材料
        for item, count in materials.items():
            player.remove_item(item, count)
            
        if success:
            # 炼器成功
            item_id = f"{item_name}_equip"
            attributes = json.loads(attributes)
            attributes = {k: int(v * attr_multiplier) for k, v in attributes.items()}
            
            # 金灵根加成
            if '金' in player.roots and random.random() < 0.15:
                attributes['durability'] = 200  # 额外耐久度
                bonus_msg = "\n金灵根触发金属亲和，装备耐久度大幅提升！"
            else:
                attributes['durability'] = 100
                bonus_msg = ""
            
            player.add_item(item_id, 1, attributes['durability'])
            
            # 炼器技能经验
            player.add_skill_exp('炼器术', 15)
            
            result = f"恭喜！你成功炼制出{item_name}({quality})！\n"
            result += "装备属性: " + ", ".join([f"{k}+{v}" for k, v in attributes.items()])
            result += bonus_msg
            
            return result
        else:
            # 炼器失败
            if random.random() < 0.2:  # 20%几率事故
                damage = random.randint(10, 20)
                player.health = max(1, player.health - damage)
                player.update()
                return f"炼器失败！炉火失控，你受到了{damage}点伤害。"
            else:
                return "炼器失败，材料全部损失。"
                
    def calculate_success_rate(self, player: Player, recipe_id: str) -> float:
        """计算炼器成功率"""
        recipe = self.db.fetch_one(
            "SELECT grade FROM forging_recipes WHERE recipe_id = ?",
            (recipe_id,)
        )
        if not recipe:
            return 0.0
            
        base_rate = {
            '法器': 0.7,
            '灵器': 0.5,
            '法宝': 0.4,
            '灵宝': 0.3,
            '仙器': 0.2,
            '神器': 0.1
        }[recipe[0]]
        
        # 炼器技能加成
        forging_skill = player.skills.get('炼器术', {}).get('level', 0)
        base_rate += forging_skill * 0.03  # 每级技能增加3%成功率
        
        # 金灵根加成
        if '金' in player.roots:
            base_rate += player.roots['金'] / 400  # 金灵根提高成功率
            
        return min(0.9, max(0.1, base_rate))  # 保持在10%-90%之间