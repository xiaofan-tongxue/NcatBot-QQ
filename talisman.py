from player import Player
from database import Database
import random
import json
from datetime import datetime, timedelta

class TalismanSystem:
    def __init__(self):
        self.db = Database()
        
    def get_learned_recipes(self, player: Player) -> list:
        """获取玩家已学习的符箓配方"""
        recipes = self.db.fetch_all(
            """SELECT t.name, t.grade, t.effect_type, t.materials, t.effect 
            FROM talisman_recipes t
            JOIN player_recipes p ON t.recipe_id = p.recipe_id
            WHERE p.qq_id = ? AND p.recipe_type = 'talisman'""",
            (player.qq_id,)
        )
        return recipes
        
    def list_recipes(self, player: Player) -> str:
        """列出玩家可用的符箓配方"""
        recipes = self.get_learned_recipes(player)
        
        if not recipes:
            return "你尚未学习任何符箓配方，请通过完成任务获取配方"
            
        result = "可制作符箓:\n"
        for name, grade, effect_type, materials, effect in recipes:
            materials = json.loads(materials)
            result += f"{name} ({grade}-{effect_type})\n"
            result += f"效果: {effect}\n"
            result += "需要材料: " + ", ".join([f"{k}x{v}" for k, v in materials.items()])
            result += "\n\n"
            
        return result
        
    def learn_recipe(self, player: Player, talisman_name: str) -> bool:
        """学习符箓配方"""
        recipe = self.db.fetch_one(
            "SELECT recipe_id FROM talisman_recipes WHERE name = ?",
            (talisman_name,)
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
            "INSERT INTO player_recipes (qq_id, recipe_type, recipe_id) VALUES (?, 'talisman', ?)",
            (player.qq_id, recipe[0])
        )
        return True
        
    def make_talisman(self, player: Player, talisman_name: str) -> str:
        """制作符箓"""
        # 查找配方
        recipe = self.db.fetch_one(
            """SELECT t.recipe_id, t.materials, t.effect, t.effect_type 
            FROM talisman_recipes t
            JOIN player_recipes p ON t.recipe_id = p.recipe_id
            WHERE p.qq_id = ? AND t.name = ?""",
            (player.qq_id, talisman_name)
        )
        if not recipe:
            return f"你尚未学习{talisman_name}的制作方法"
            
        recipe_id, materials, effect, effect_type = recipe
        materials = json.loads(materials)
        
        # 检查材料
        for item, count in materials.items():
            if player.items.get(item, {}).get('count', 0) < count:
                return f"材料不足，需要{item}x{count}"
                
        # 计算成功率
        success_rate = self.calculate_success_rate(player, recipe_id, effect_type)
        quality_rate = random.random()
        
        # 确定符箓品质
        if quality_rate < 0.1:
            quality = "极品"
            effect_multiplier = 1.3
        elif quality_rate < 0.3:
            quality = "上"
            effect_multiplier = 1.15
        elif quality_rate < 0.6:
            quality = "中"
            effect_multiplier = 1.0
        else:
            quality = "下"
            effect_multiplier = 0.85
            
        success = random.random() < success_rate
        
        # 消耗材料
        for item, count in materials.items():
            player.remove_item(item, count)
            
        if success:
            # 制符成功
            talisman_id = f"{talisman_name}_{quality}"
            player.add_item(talisman_id, 1)
            
            # 水灵根加成
            if '水' in player.roots and effect_type in ['辅助', '特殊']:
                extra_talisman = f"{talisman_name}_{quality}"
                player.add_item(extra_talisman, 1)
                bonus_msg = "\n水灵根触发符水亲和，额外获得一张符箓！"
            else:
                bonus_msg = ""
            
            # 制符技能经验
            player.add_skill_exp('制符术', 8)
            
            result = f"恭喜！你成功制作出{talisman_name}({quality})！\n"
            result += f"效果: {effect} (效果提升{int((effect_multiplier-1)*100)}%)"
            result += bonus_msg
            
            return result
        else:
            # 制符失败
            if random.random() < 0.1:  # 10%几率反噬
                mana_loss = random.randint(10, 30)
                player.mana = max(0, player.mana - mana_loss)
                player.update()
                return f"制符失败！灵力反噬，你损失了{mana_loss}点真元。"
            else:
                return "制符失败，材料全部损失。"
                
    def calculate_success_rate(self, player: Player, recipe_id: str, effect_type: str) -> float:
        """计算制符成功率"""
        recipe = self.db.fetch_one(
            "SELECT grade FROM talisman_recipes WHERE recipe_id = ?",
            (recipe_id,)
        )
        if not recipe:
            return 0.0
            
        base_rate = {
            '黄符': 0.8,
            '朱砂符': 0.6,
            '玉符': 0.4,
            '血骨符': 0.3
        }[recipe[0]]
        
        # 制符技能加成
        talisman_skill = player.skills.get('制符术', {}).get('level', 0)
        base_rate += talisman_skill * 0.04  # 每级技能增加4%成功率
        
        # 水灵根对辅助符加成
        if '水' in player.roots and effect_type in ['辅助', '特殊']:
            base_rate += player.roots['水'] / 400
            
        # 火灵根对攻击符加成
        if '火' in player.roots and effect_type == '攻击':
            base_rate += player.roots['火'] / 500
            
        return min(0.95, max(0.05, base_rate))  # 保持在5%-95%之间