from database import Database
import random

class MaterialSystem:
    def __init__(self):
        self.db = Database()
        
    def get_monster_drops(self, monster_level: str) -> dict:
        """获取妖兽掉落材料"""
        materials = self.db.fetch_all(
            "SELECT material_id, name FROM material_sources WHERE source_type = 'monster' AND source_level = ?",
            (monster_level,)
        )
        return {m[0]: m[1] for m in materials} if materials else {}
        
    def random_drop(self, monster_level: str) -> str:
        """随机掉落材料"""
        drop_info = self.db.fetch_one(
            "SELECT material_id, drop_rate FROM material_sources WHERE source_type = 'monster' AND source_level = ?",
            (monster_level,)
        )
        
        if drop_info and random.random() < drop_info[1]:
            return drop_info[0]
        return None
        
    def get_quest_rewards(self, quest_level: str) -> dict:
        """获取任务奖励材料"""
        materials = self.db.fetch_all(
            "SELECT material_id, name FROM material_sources WHERE source_type = 'quest' AND source_level = ?",
            (quest_level,)
        )
        return {m[0]: m[1] for m in materials} if materials else {}