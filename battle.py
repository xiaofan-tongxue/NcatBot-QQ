import json
from player import Player
from database import Database
import random
from datetime import datetime, timedelta

class BattleSystem:
    ELEMENT_WEAKNESS = {
        '金': '木',
        '木': '土',
        '土': '水',
        '水': '火',
        '火': '金'
    }
    
    def __init__(self):
        self.db = Database()
        
    def battle(self, attacker: Player, defender_id: str) -> str:
        """玩家之间的战斗"""
        if attacker.qq_id == defender_id:
            return "你不能与自己战斗"
            
        defender = Player(defender_id)
        if not defender.name:
            defender.close()
            return "找不到对手"
            
        # 检查战斗冷却
        if attacker.last_battle:
            last_time = datetime.strptime(attacker.last_battle, "%Y-%m-%d %H:%M:%S")
            if (datetime.now() - last_time) < timedelta(minutes=30):
                defender.close()
                return "战斗过于频繁，需要休息30分钟后再战"
        
        # 计算基础属性
        att_stats = self.calculate_battle_stats(attacker)
        def_stats = self.calculate_battle_stats(defender)
        
        # 战斗过程 (简化版3回合制)
        log = []
        att_hp, def_hp = attacker.health, defender.health
        att_mana, def_mana = attacker.mana, defender.mana
        
        for round in range(1, 4):
            # 攻击方回合
            att_dmg = self.calculate_damage(attacker, defender, att_stats)
            def_hp -= att_dmg
            log.append(f"第{round}回合，{attacker.name}造成{att_dmg}点伤害")
            
            if def_hp <= 0:
                log.append(f"{defender.name}不敌落败！")
                break
                
            # 防御方回合
            def_dmg = self.calculate_damage(defender, attacker, def_stats)
            att_hp -= def_dmg
            log.append(f"{defender.name}反击造成{def_dmg}点伤害")
            
            if att_hp <= 0:
                log.append(f"{attacker.name}不敌落败！")
                break
                
        # 确定胜负
        if att_hp > def_hp:
            winner, loser = attacker, defender
            result = "胜利"
        else:
            winner, loser = defender, attacker
            result = "失败"
            
        # 更新玩家状态
        attacker.health = max(1, att_hp)
        defender.health = max(1, def_hp)
        attacker.last_battle = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 战斗奖励/惩罚
        gold_transfer = min(50, loser.gold)
        attacker.gold += gold_transfer
        loser.gold -= gold_transfer
        
        # 记录战斗日志
        self.db.execute(
            """INSERT INTO battle_logs 
            (qq_id, opponent_id, result, details, battle_time)
            VALUES (?, ?, ?, ?, ?)""",
            (attacker.qq_id, defender.qq_id, result, "\n".join(log), 
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        
        # 更新玩家数据
        attacker.update()
        defender.update()
        defender.close()
        
        # 返回战斗结果
        battle_result = f"战斗结果: {attacker.name} {result}\n"
        battle_result += f"获得灵石: {gold_transfer if result == '胜利' else 0}\n"
        battle_result += "战斗过程:\n" + "\n".join(log)
        
        return battle_result
        
    def calculate_battle_stats(self, player: Player) -> dict:
        """计算战斗属性"""
        stats = {
            'attack': player.attack,
            'defense': player.defense,
            'speed': player.speed,
            'element_affinity': self.get_element_affinity(player)
        }
        
        # 装备加成
        for item_id, data in player.items.items():
            if item_id.endswith('_equip'):
                # 假设装备ID以_equip结尾
                item_stats = self.db.fetch_one(
                    "SELECT attributes FROM forging_recipes WHERE name = ?", 
                    (item_id[:-6],)
                )
                if item_stats:
                    attributes = json.loads(item_stats[0])
                    for attr, value in attributes.items():
                        stats[attr] = stats.get(attr, 0) + value
                        
        return stats
        
    def get_element_affinity(self, player: Player) -> str:
        """获取玩家主元素属性"""
        if not player.roots:
            return None
            
        # 返回纯度最高的灵根
        return max(player.roots.items(), key=lambda x: x[1])[0]
        
    def calculate_damage(self, attacker: Player, defender: Player, att_stats: dict) -> int:
        """计算伤害"""
        base_dmg = max(1, att_stats['attack'] - defender.defense // 2)
        
        # 元素克制加成
        att_element = self.get_element_affinity(attacker)
        def_element = self.get_element_affinity(defender)
        
        if att_element and def_element and self.ELEMENT_WEAKNESS.get(att_element) == def_element:
            base_dmg = int(base_dmg * 1.5)
            
        # 随机波动
        dmg = random.randint(int(base_dmg * 0.8), int(base_dmg * 1.2))
        
        return max(1, dmg)