from player import Player
from database import Database
import random
import json
from datetime import datetime, timedelta

class QuestSystem:
    def __init__(self):
        self.db = Database()
        self.quest_refresh_interval = timedelta(minutes=30)
        self.last_refresh_time = None
        
    def refresh_quests(self):
        """每半小时刷新一次任务"""
        now = datetime.now()
        if self.last_refresh_time and (now - self.last_refresh_time) < self.quest_refresh_interval:
            return
            
        self.last_refresh_time = now
        
        # 清除过期任务
        self.db.execute(
            "DELETE FROM active_quests WHERE expire_time < ?",
            (now.strftime("%Y-%m-%d %H:%M:%S"),)
        )
        
        # 为每个玩家生成新任务（确保每个等级一个）
        players = self.db.fetch_all("SELECT qq_id, realm FROM players")
        for qq_id, realm in players:
            # 下等任务（所有境界）
            self.assign_quest(qq_id, realm, '下等')
            
            # 中等任务（金丹境/结魔丹以上）
            if realm in ['金丹境', '结魔丹', '元婴境', '化魔胎', '化神境', '炼狱境', '渡劫境', '逆天境', '大乘境', '灭世境']:
                self.assign_quest(qq_id, realm, '中等')
                
            # 上等任务（化神境/炼狱境以上）
            if realm in ['化神境', '炼狱境', '渡劫境', '逆天境', '大乘境', '灭世境']:
                self.assign_quest(qq_id, realm, '上等')
    
    def assign_quest(self, qq_id: str, realm: str, level: str):
        """为玩家分配指定等级的任务"""
        # 检查是否已有该等级任务
        existing = self.db.fetch_one(
            """SELECT 1 FROM active_quests a
            JOIN quests q ON a.quest_id = q.quest_id
            WHERE a.qq_id = ? AND q.level = ?""",
            (qq_id, level)
        )
        if existing:
            return
            
        # 随机获取一个符合要求的任务
        quest = self.db.fetch_one(
            """SELECT quest_id FROM quests 
            WHERE level = ? AND (required_realm IS NULL OR required_realm <= ?)
            ORDER BY RANDOM() LIMIT 1""",
            (level, realm)
        )
        
        if quest:
            expire_time = datetime.now() + timedelta(hours=2)
            self.db.execute(
                "INSERT INTO active_quests (quest_id, qq_id, expire_time) VALUES (?, ?, ?)",
                (quest[0], qq_id, expire_time.strftime("%Y-%m-%d %H:%M:%S"))
            )
    
    def get_available_quests(self, player: Player) -> str:
        """获取玩家可接任务"""
        self.refresh_quests()
        
        quests = self.db.fetch_all(
            """SELECT q.quest_id, q.name, q.type, q.level, q.objectives 
            FROM quests q JOIN active_quests a ON q.quest_id = a.quest_id
            WHERE a.qq_id = ?""",
            (player.qq_id,)
        )
        
        if not quests:
            return "当前没有可接的任务"
            
        result = "可接任务:\n"
        for quest in quests:
            objectives = json.loads(quest[4])
            obj_text = ", ".join([f"{k}: {v}" for k, v in objectives.items()])
            result += f"{quest[1]} ({quest[2]}-{quest[3]})\n目标: {obj_text}\n\n"
            
        return result
    
    def accept_quest(self, player: Player, quest_name: str) -> str:
        """接受任务"""
        # 查找任务
        quest_data = self.db.fetch_one(
            """SELECT q.quest_id, q.required_level, q.required_faction 
            FROM quests q JOIN active_quests a ON q.quest_id = a.quest_id
            WHERE q.name = ? AND a.qq_id = ?""",
            (quest_name, player.qq_id)
        )
        
        if not quest_data:
            return f"找不到任务: {quest_name}"
            
        quest_id, req_level, req_faction = quest_data
        
        # 检查是否已接受
        existing = self.db.fetch_one(
            "SELECT 1 FROM player_quests WHERE qq_id = ? AND quest_id = ?",
            (player.qq_id, quest_id)
        )
        if existing:
            return "你已经接受过这个任务了"
            
        # 检查条件
        if self.db.REALMS.index(player.realm) + 1 < req_level:
            return f"你的境界不足，需要{self.db.REALMS[req_level-1]}"
            
        if req_faction and req_faction != player.faction:
            return f"此任务需要{req_faction}阵营"
            
        # 接受任务
        self.db.execute(
            "INSERT INTO player_quests (qq_id, quest_id) VALUES (?, ?)",
            (player.qq_id, quest_id)
        )
        
        # 更新玩家任务缓存
        quest_info = self.db.fetch_one(
            "SELECT name, type FROM quests WHERE quest_id = ?", (quest_id,)
        )
        if quest_info:
            player.quests[quest_id] = {
                'name': quest_info[0],
                'type': quest_info[1],
                'progress': {},
                'is_completed': False
            }
        
        return f"你已接受任务: {quest_name}"
        
    def complete_quest(self, player: Player, quest_name: str) -> str:
        """完成任务并发放奖励"""
        quest_data = self.db.fetch_one(
            """SELECT q.quest_id, q.rewards, q.reward_type 
            FROM quests q JOIN player_quests pq ON q.quest_id = pq.quest_id
            WHERE q.name = ? AND pq.qq_id = ? AND pq.is_completed = FALSE""",
            (quest_name, player.qq_id)
        )
        
        if not quest_data:
            return f"找不到未完成的任务: {quest_name}"
            
        quest_id, rewards, reward_type = quest_data
        
        # 检查任务进度
        progress_data = self.db.fetch_one(
            "SELECT progress FROM player_quests WHERE qq_id = ? AND quest_id = ?",
            (player.qq_id, quest_id)
        )
        if not progress_data or not progress_data[0]:
            progress = {}
        else:
            progress = json.loads(progress_data[0])
            
        # 验证是否完成所有目标
        objectives = self.db.fetch_one(
            "SELECT objectives FROM quests WHERE quest_id = ?", (quest_id,)
        )
        objectives = json.loads(objectives[0])
        
        for objective, required in objectives.items():
            if progress.get(objective, 0) < required:
                return f"任务未完成，还需要{objective} {required - progress.get(objective, 0)}次"
                
        # 发放奖励
        if reward_type in ['alchemy', 'forging', 'talisman']:
            # 获取随机配方
            recipe = self.get_random_recipe(reward_type, player.realm)
            recipe_item_id = f"{recipe['name']}配方"
            
            # 添加配方到背包
            player.add_item(recipe_item_id, 1, is_recipe=True, recipe_type=reward_type)
            reward_msg = f"获得配方: {recipe['name']}"
        else:
            # 普通物品奖励
            rewards = json.loads(rewards)
            reward_msg = "获得奖励: "
            if 'gold' in rewards:
                player.gold += rewards['gold']
                reward_msg += f"{rewards['gold']}灵石, "
                
            if 'items' in rewards:
                for item, count in rewards['items'].items():
                    player.add_item(item, count)
                    reward_msg += f"{item}x{count}, "
                reward_msg = reward_msg[:-2]  # 去除最后的逗号和空格
        
        # 标记任务完成
        self.db.execute(
            """UPDATE player_quests 
            SET is_completed = TRUE, complete_time = ?
            WHERE qq_id = ? AND quest_id = ?""",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), player.qq_id, quest_id)
        )
        
        # 更新玩家任务缓存
        player.quests[quest_id]['is_completed'] = True
        
        return f"恭喜完成任务{quest_name}！{reward_msg}"
    
    def get_random_recipe(self, recipe_type: str, realm: str) -> dict:
        """根据境界获取随机配方"""
        # 优先给当前境界突破所需的配方
        breakthrough_recipes = {
            '炼体境': '筑基丹',
            '蚀骨境': '聚煞丹',
            '练气境': '凝气丹',
            '聚煞境': '魔煞丹',
            '筑基境': '金丹',
            '铸魔台': '魔心丹',
            '金丹境': '元婴丹',
            '结魔丹': '化魔丹',
            '元婴境': '化神丹',
            '化魔胎': '炼狱丹',
            '化神境': '渡劫丹',
            '炼狱境': '逆天丹',
            '渡劫境': '大乘丹',
            '逆天境': '灭世丹'
        }
        
        if realm in breakthrough_recipes:
            recipe_name = breakthrough_recipes[realm]
            recipe = self.db.fetch_one(
                f"SELECT * FROM {recipe_type}_recipes WHERE name = ?",
                (recipe_name,)
            )
            if recipe:
                return {
                    'id': recipe[0],
                    'name': recipe_name,
                    'type': recipe_type
                }
        
        # 随机获取一个配方
        table = f"{recipe_type}_recipes"
        recipe = self.db.fetch_one(
            f"SELECT * FROM {table} ORDER BY RANDOM() LIMIT 1"
        )
        
        return {
            'id': recipe[0],
            'name': recipe[1],
            'type': recipe_type
        }