from player import Player
from database import Database
import random
import json

class CombatSystem:
    def __init__(self):
        self.db = Database()
        
    def list_monsters(self, player: Player) -> str:
        """列出可挑战的妖兽（根据境界）"""
        monsters = self.db.fetch_all(
            """SELECT name, level FROM monsters 
            WHERE realm_requirement <= ?
            ORDER BY level""",
            (player.realm,)
        )

        if not monsters:
            return "当前没有可挑战的妖兽"
            
        result = "可挑战的妖兽：\n"
        for i, (name, level) in enumerate(monsters, 1):
            level_name = {'low': '低级', 'medium': '中级', 'high': '顶级'}[level]
            result += f"{i}. {name} ({level_name})\n"
        return result
        
    def battle_monster(self, player: Player, monster_name: str) -> str:
        """与妖兽战斗"""
        try:
            # 获取妖兽数据
            monster_data = self.db.fetch_one(
                "SELECT * FROM monsters WHERE name = ? AND realm_requirement <= ?",
                (monster_name, player.realm))
            if not monster_data:
                return f"找不到妖兽：{monster_name} 或你的境界不足"
                
            # 解析掉落物品JSON
            try:
                drop_items = json.loads(monster_data[6])  # 第7列是drop_items
            except json.JSONDecodeError:
                return "妖兽数据异常，请联系管理员"
                
            monster = {
                'monster_id': monster_data[0],
                'name': monster_data[1],
                'level': monster_data[2],
                'health': monster_data[3],
                'attack': monster_data[4],
                'defense': monster_data[5],
                'drop_items': drop_items
            }
            
            # 简单战斗模拟
            player_power = player.attack + player.defense
            monster_power = monster['attack'] + monster['defense']
            
            # 战斗结果
            if player_power >= monster_power * 0.8:  # 80%强度即可胜利
                # 计算掉落
                drops = []
                for item, rate in monster['drop_items'].items():
                    if random.random() < rate:
                        drops.append(item)
                        
                # 添加物品到玩家背包
                if drops:
                    for item in drops:
                        player.add_item(item, 1)
                        
                # 扣除玩家气血
                damage = max(1, monster['attack'] - player.defense // 2)
                player.health = max(1, player.health - damage)
                player.update()
                
                result = f"你战胜了{monster['name']}！"
                if drops:
                    result += f"\n获得：{', '.join(drops)}"
                result += f"\n受到{damage}点伤害"
                
                # 更新任务进度
                player.update_quest_progress('kill_monster', 1)
                return result
            else:
                # 战斗失败
                damage = monster['attack']
                player.health = max(1, player.health - damage)
                player.update()
                return f"不敌{monster['name']}！受到{damage}点伤害"
                
        except Exception as e:
            return f"战斗过程中发生错误：{str(e)}"