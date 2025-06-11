from player import Player
from database import Database
import random
import json
from datetime import datetime, timedelta

class AlchemySystem:
    def __init__(self):
        self.db = Database()
        
    def get_learned_recipes(self, player: Player) -> list:
        """获取玩家已学习的丹方"""
        recipes = self.db.fetch_all(
            """SELECT a.name, a.grade, a.sub_grade, a.ingredients, a.effect 
            FROM alchemy_recipes a
            JOIN player_recipes p ON a.recipe_id = p.recipe_id
            WHERE p.qq_id = ? AND p.recipe_type = 'alchemy'""",
            (player.qq_id,)
        )
        return recipes
        
    def list_recipes(self, player: Player) -> str:
        """列出玩家已学习的丹方"""
        recipes = self.get_learned_recipes(player)
        
        if not recipes:
            return "你尚未学习任何丹方，请通过完成任务获取丹方"
            
        result = "已学丹方:\n"
        for name, grade, sub_grade, ingredients, effect in recipes:
            ingredients = json.loads(ingredients)
            result += f"{name} ({grade}{sub_grade}) - 效果: {effect}\n"
            result += "需要材料: " + ", ".join([f"{k}x{v}" for k, v in ingredients.items()]) + "\n\n"
            
        return result
        
    def learn_recipe(self, player: Player, recipe_name: str) -> bool:
        """学习丹方"""
        recipe = self.db.fetch_one(
            "SELECT recipe_id FROM alchemy_recipes WHERE name = ?",
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
            "INSERT INTO player_recipes (qq_id, recipe_type, recipe_id) VALUES (?, 'alchemy', ?)",
            (player.qq_id, recipe[0])
        )
        return True
        
    def refine_pill(self, player: Player, pill_name: str) -> str:
        """炼制丹药"""
        # 检查是否已学习该配方
        recipe = self.db.fetch_one(
            """SELECT a.recipe_id, a.ingredients, a.effect 
            FROM alchemy_recipes a
            JOIN player_recipes p ON a.recipe_id = p.recipe_id
            WHERE p.qq_id = ? AND a.name = ?""",
            (player.qq_id, pill_name)
        )
        if not recipe:
            return f"你尚未学习{pill_name}的炼制方法"
            
        recipe_id, ingredients, effect = recipe
        ingredients = json.loads(ingredients)
        
        # 检查材料
        for item, count in ingredients.items():
            if player.items.get(item, {}).get('count', 0) < count:
                return f"材料不足，需要{item}x{count}"
                
        # 计算成功率
        success_rate = self.calculate_success_rate(player, pill_name)
        quality_rate = random.random()
        
        # 确定丹药品质
        if quality_rate < 0.1:
            quality = "极品"
        elif quality_rate < 0.3:
            quality = "上"
        elif quality_rate < 0.6:
            quality = "中"
        else:
            quality = "下"
            
        success = random.random() < success_rate
        
        # 消耗材料
        for item, count in ingredients.items():
            player.remove_item(item, count)
            
        if success:
            # 炼丹成功
            pill_id = f"{pill_name}_{quality}"
            player.add_item(pill_id, 1)
            
            # 灵根经验加成
            if '火' in player.roots:
                player.add_skill_exp('炼丹术', 10 + player.roots['火'] // 10)
            else:
                player.add_skill_exp('炼丹术', 10)
            
            result = f"恭喜！你成功炼制出{pill_name}({quality})！"
            
            # 特殊灵根效果
            if '木' in player.roots and random.random() < 0.1:
                extra_pill = f"{pill_name}_{quality}"
                player.add_item(extra_pill, 1)
                result += "\n木灵根触发灵药亲和，额外获得一枚丹药！"
                
            return result
        else:
            # 炼丹失败
            if random.random() < 0.3:  # 30%几率炸炉
                damage = random.randint(5, 15)
                player.health = max(1, player.health - damage)
                player.update()
                return f"炼丹失败！丹炉爆炸，你受到了{damage}点伤害。"
            else:
                return "炼丹失败，材料全部损失。"
                
    def calculate_success_rate(self, player: Player, pill_name: str) -> float:
        """计算炼丹成功率"""
        recipe = self.db.fetch_one(
            "SELECT grade FROM alchemy_recipes WHERE name = ?",
            (pill_name,)
        )
        if not recipe:
            return 0.0
            
        base_rate = {
            '凡品': 0.8,
            '灵品': 0.6,
            '仙品': 0.4,
            '神品': 0.2
        }[recipe[0]]
        
        # 炼丹技能加成
        alchemy_skill = player.skills.get('炼丹术', {}).get('level', 0)
        base_rate += alchemy_skill * 0.05  # 每级技能增加5%成功率
        
        # 火灵根加成
        if '火' in player.roots:
            base_rate += player.roots['火'] / 500  # 火灵根提高成功率
            
        # 木灵根小幅加成
        if '木' in player.roots:
            base_rate += player.roots['木'] / 1000
            
        return min(0.95, max(0.05, base_rate))  # 保持在5%-95%之间