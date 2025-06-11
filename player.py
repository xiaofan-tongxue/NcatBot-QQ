from datetime import datetime, timedelta
from database import Database
import json
import random

class Player:
    REALMS = {
        '仙域': [
            '炼体境', '练气境', '筑基境', '金丹境', 
            '元婴境', '化神境', '渡劫境', '大乘境'
        ],
        '魔渊': [
            '蚀骨境', '聚煞境', '铸魔台', '结魔丹',
            '化魔胎', '炼狱境', '逆天境', '灭世境'
        ],
        '中立': [
            '炼体境', '练气境', '筑基境', '金丹境',
            '元婴境', '化神境', '渡劫境', '大乘境'
        ]
    }
    
    STAGES = ['初期', '中期', '后期', '大圆满']
    
    def __init__(self, qq_id: str, qq_nickname: str):
        self.db = Database()
        self.qq_id = qq_id
        self.load_data(qq_nickname)

    def load_data(self, current_nickname: str):
        """加载玩家数据，总是使用最新QQ昵称"""
        player_data = self.db.fetch_one(
            "SELECT * FROM players WHERE qq_id = ?", 
            (self.qq_id,)
        )

        if not player_data:
            self.initialize_new_player(current_nickname)
        else:
            # 更新为最新QQ昵称
            self.name = current_nickname
            self.qq_nickname = player_data[2]  # 获取 qq_nickname 字段
            self.faction = player_data[3]
            self.realm = player_data[4]
            self.stage = player_data[5]
            self.cultivation = player_data[6]
            self.health = player_data[7]
            self.max_health = player_data[8]
            self.mana = player_data[9]
            self.max_mana = player_data[10]
            self.attack = player_data[11]
            self.defense = player_data[12]
            self.speed = player_data[13]
            self.gold = player_data[14]
            self.create_time = player_data[15]
            self.last_active = player_data[16]
            self.last_cultivate = player_data[17] if player_data[17] else ""
            self.last_battle = player_data[18] if player_data[18] else ""
            self.is_cultivating = bool(player_data[19]) if player_data[19] is not None else False
            self.cultivate_start_time = player_data[20] if player_data[20] else None
            self.daily_cultivate_count = player_data[21] if player_data[21] is not None else 0
            self.last_breakthrough_attempt = player_data[22] if player_data[22] else None

            # 更新数据库中的名字
            self.db.execute(
                "UPDATE players SET name = ?, qq_nickname = ? WHERE qq_id = ?",
                (current_nickname, current_nickname, self.qq_id)
            )

        # 加载其他数据
        self.roots = self.load_spiritual_roots()
        self.skills = self.load_skills()
        self.items = self.load_items()
        self.quests = self.load_quests()
        
    def initialize_new_player(self, qq_nickname: str):
        """初始化新玩家，使用QQ昵称"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.name = qq_nickname  # 直接使用QQ昵称
        self.faction = "中立"
        self.realm = "炼体境"
        self.stage = "初期"
        self.cultivation = 0
        self.health = 100
        self.max_health = 100
        self.mana = 100
        self.max_mana = 100
        self.attack = 10
        self.defense = 5
        self.speed = 5
        self.gold = 100
        self.create_time = now
        self.last_active = now
        self.last_cultivate = None
        self.last_battle = None
        self.is_cultivating = False
        self.cultivate_start_time = None
        self.daily_cultivate_count = 0
        self.last_breakthrough_attempt = None
        
        # 随机生成灵根
        root_types = ['金', '木', '水', '火', '土']
        main_root = random.choice(root_types)
        purity = random.randint(60, 90)
        
        self.db.execute(
            """INSERT INTO players 
            (qq_id, name, faction, realm, stage, cultivation, health, max_health, 
             mana, max_mana, attack, defense, speed, gold, create_time, last_active,
             is_cultivating, cultivate_start_time, daily_cultivate_count, last_breakthrough_attempt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (self.qq_id, self.name, self.faction, self.realm, self.stage, 
             self.cultivation, self.health, self.max_health, self.mana, 
             self.max_mana, self.attack, self.defense, self.speed, 
             self.gold, self.create_time, self.last_active,
             self.is_cultivating, self.cultivate_start_time, self.daily_cultivate_count,
             self.last_breakthrough_attempt)
        )
        
        # 添加灵根
        self.db.execute(
            "INSERT INTO spiritual_roots (qq_id, root_type, purity) VALUES (?, ?, ?)",
            (self.qq_id, main_root, purity)
        )
        
        # 添加初始技能
        initial_skills = ['基础吐纳', '基础剑法']
        for skill in initial_skills:
            self.db.execute(
                "INSERT INTO skills (qq_id, skill_id, level) VALUES (?, ?, 1)",
                (self.qq_id, skill)
            )
        
        # 添加初始物品
        initial_items = {'灵草': 5, '符纸': 10, '朱砂': 5}
        for item, count in initial_items.items():
            self.db.execute(
                "INSERT INTO items (qq_id, item_id, count) VALUES (?, ?, ?)",
                (self.qq_id, item, count)
            )
        
        # 接受初始任务
        self.db.execute(
            "INSERT INTO player_quests (qq_id, quest_id) VALUES (?, 'main_1')",
            (self.qq_id,)
        )
        
        self.roots = {main_root: purity}
        self.skills = {skill: {'level': 1, 'exp': 0} for skill in initial_skills}
        self.items = initial_items
        self.quests = {'main_1': {'progress': {}, 'is_completed': False}}
        
    def load_spiritual_roots(self):
        roots_data = self.db.fetch_all(
            "SELECT root_type, purity FROM spiritual_roots WHERE qq_id = ?", (self.qq_id,)
        )
        return {root[0]: root[1] for root in roots_data} if roots_data else {}
        
    def load_skills(self):
        skills_data = self.db.fetch_all(
            "SELECT skill_id, level, exp FROM skills WHERE qq_id = ?", (self.qq_id,)
        )
        return {skill[0]: {'level': skill[1], 'exp': skill[2]} for skill in skills_data} if skills_data else {}
        
    def load_items(self):
        items_data = self.db.fetch_all(
            "SELECT item_id, count, durability FROM items WHERE qq_id = ?", (self.qq_id,)
        )
        return {item[0]: {'count': item[1], 'durability': item[2]} for item in items_data} if items_data else {}
        
    def load_quests(self):
        quests_data = self.db.fetch_all(
            """SELECT q.quest_id, q.name, q.type, pq.progress, pq.is_completed 
            FROM player_quests pq JOIN quests q ON pq.quest_id = q.quest_id 
            WHERE pq.qq_id = ?""", (self.qq_id,)
        )
        return {quest[0]: {
            'name': quest[1],
            'type': quest[2],
            'progress': json.loads(quest[3]) if quest[3] else {},
            'is_completed': bool(quest[4])
        } for quest in quests_data} if quests_data else {}
        
    def update(self):
        self.db.execute(
            """UPDATE players 
            SET name=?, faction=?, realm=?, stage=?, cultivation=?, 
                health=?, max_health=?, mana=?, max_mana=?, 
                attack=?, defense=?, speed=?, gold=?, last_active=?,
                is_cultivating=?, cultivate_start_time=?, daily_cultivate_count=?,
                last_breakthrough_attempt=?
            WHERE qq_id=?""",
            (self.name, self.faction, self.realm, self.stage, self.cultivation,
             self.health, self.max_health, self.mana, self.max_mana,
             self.attack, self.defense, self.speed, self.gold,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             self.is_cultivating, self.cultivate_start_time, self.daily_cultivate_count,
             self.last_breakthrough_attempt,
             self.qq_id)
        )
        
    def start_cultivation(self):
        """开始修炼"""
        self.is_cultivating = True
        self.cultivate_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 更新每日修炼次数
        today = datetime.now().strftime("%Y-%m-%d")
        if self.last_cultivate and self.last_cultivate.startswith(today):
            self.daily_cultivate_count += 1
        else:
            self.daily_cultivate_count = 1
            
        self.last_cultivate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.update()
        
    def complete_cultivation(self):
        """完成修炼"""
        self.is_cultivating = False
        self.cultivate_start_time = None
        self.update()
        
    def add_item(self, item_id: str, count: int = 1, durability: int = None):
        if item_id in self.items:
            self.db.execute(
                "UPDATE items SET count = count + ? WHERE qq_id = ? AND item_id = ?",
                (count, self.qq_id, item_id)
            )
            self.items[item_id]['count'] += count
        else:
            self.db.execute(
                "INSERT INTO items (qq_id, item_id, count, durability) VALUES (?, ?, ?, ?)",
                (self.qq_id, item_id, count, durability)
            )
            self.items[item_id] = {'count': count, 'durability': durability}
            
    def remove_item(self, item_id: str, count: int = 1) -> bool:
        if item_id not in self.items or self.items[item_id]['count'] < count:
            return False
            
        if self.items[item_id]['count'] == count:
            self.db.execute(
                "DELETE FROM items WHERE qq_id = ? AND item_id = ?",
                (self.qq_id, item_id)
            )
            del self.items[item_id]
        else:
            self.db.execute(
                "UPDATE items SET count = count - ? WHERE qq_id = ? AND item_id = ?",
                (count, self.qq_id, item_id)
            )
            self.items[item_id]['count'] -= count
            
        return True
        
    def add_skill_exp(self, skill_id: str, exp: int):
        if skill_id not in self.skills:
            self.db.execute(
                "INSERT INTO skills (qq_id, skill_id, level, exp) VALUES (?, ?, 1, ?)",
                (self.qq_id, skill_id, exp)
            )
            self.skills[skill_id] = {'level': 1, 'exp': exp}
        else:
            new_exp = self.skills[skill_id]['exp'] + exp
            level_up = (new_exp // 100) > (self.skills[skill_id]['exp'] // 100)
            
            self.db.execute(
                "UPDATE skills SET exp = exp + ? WHERE qq_id = ? AND skill_id = ?",
                (exp, self.qq_id, skill_id)
            )
            self.skills[skill_id]['exp'] = new_exp
            
            if level_up:
                new_level = self.skills[skill_id]['exp'] // 100 + 1
                self.db.execute(
                    "UPDATE skills SET level = ? WHERE qq_id = ? AND skill_id = ?",
                    (new_level, self.qq_id, skill_id)
                )
                self.skills[skill_id]['level'] = new_level
                return True
                
        return False
        
    def update_quest_progress(self, quest_id: str, progress: dict):
        current = self.quests.get(quest_id, {}).get('progress', {})
        for key, value in progress.items():
            current[key] = current.get(key, 0) + value
            
        self.db.execute(
            "UPDATE player_quests SET progress = ? WHERE qq_id = ? AND quest_id = ?",
            (json.dumps(current), self.qq_id, quest_id)
        )
        
        if quest_id in self.quests:
            self.quests[quest_id]['progress'] = current
        else:
            quest_data = self.db.fetch_one(
                "SELECT name, type FROM quests WHERE quest_id = ?", (quest_id,)
            )
            if quest_data:
                self.quests[quest_id] = {
                    'name': quest_data[0],
                    'type': quest_data[1],
                    'progress': current,
                    'is_completed': False
                }
                
    def complete_quest(self, quest_id: str):
        self.db.execute(
            """UPDATE player_quests 
            SET is_completed = TRUE, complete_time = ?
            WHERE qq_id = ? AND quest_id = ?""",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.qq_id, quest_id)
        )
        
        if quest_id in self.quests:
            self.quests[quest_id]['is_completed'] = True
            
    def get_status(self):
        """获取玩家状态信息"""
        status = f"{self.name} ({self.faction}阵营)\n"
        status += f"境界: {self.realm}-{self.stage}\n"
        status += f"修为: {self.get_cultivation_progress():.1f}%\n"
        status += f"生命: {self.health}/{self.max_health}\n"
        status += f"真元: {self.mana}/{self.max_mana}\n"
        status += f"攻击: {self.attack} 防御: {self.defense} 速度: {self.speed}\n"
        status += f"灵石: {self.gold}\n"
        status += "灵根: " + ", ".join([f"{k}({v}%)" for k, v in self.roots.items()])
        if self.is_cultivating:
            status += "\n状态: 正在修炼中"
        return status
        
    def get_cultivation_progress(self):
        """获取当前境界修炼进度百分比"""
        # 根据阵营获取对应的境界列表
        realms_list = self.REALMS.get(self.faction, self.REALMS['中立'])
        
        # 确保境界列表是一个列表，而不是字典
        if isinstance(realms_list, list):
            try:
                realm_index = realms_list.index(self.realm)
                base_exp = 100 * (2 ** realm_index)
                return min(100, (self.cultivation / base_exp) * 100)
            except ValueError:
                # 如果境界不在列表中，返回0
                return 0
        else:
            # 如果获取到的不是列表，记录错误并返回0
            return 0
        
    def get_next_realm(self):
        """获取下一个大境界，根据阵营返回"""
        current_realms = self.REALMS.get(self.faction, self.REALMS['中立'])
        current_index = current_realms.index(self.realm)
        if current_index + 1 < len(current_realms):
            return current_realms[current_index + 1]
        return None
    
    def get_inventory(self):
        """获取玩家的储物袋信息"""
        inventory = []
        for item, data in self.items.items():
            count = data['count']
            durability = data['durability']
            if durability is not None:
                inventory.append(f"{item} x{count} (耐久度: {durability})")
            else:
                inventory.append(f"{item} x{count}")
        if not inventory:
            return "储物袋为空"
        return "储物袋内容:\n" + "\n".join(inventory)
        
    def transfer_item(self, item_name, count, target_player):
        """转移道具给其他玩家"""
        if item_name not in self.items:
            return f"你没有此道具或道具名错误: {item_name}"
        if self.items[item_name]['count'] < count:
            return f"你储物袋内{item_name}不足，无法赠送 {count} 个"
        if self.qq_id == target_player.qq_id:
            return "自己的道具无法赠送给自己"

        # 减少当前玩家的道具数量
        self.items[item_name]['count'] -= count
        self.db.execute(
            "UPDATE items SET count = ? WHERE qq_id = ? AND item_id = ?",
            (self.items[item_name]['count'], self.qq_id, item_name)
        )

        # 增加目标玩家的道具数量
        if item_name in target_player.items:
            target_player.items[item_name]['count'] += count
            target_player.db.execute(
                "UPDATE items SET count = ? WHERE qq_id = ? AND item_id = ?",
                (target_player.items[item_name]['count'], target_player.qq_id, item_name)
            )
        else:
            target_player.items[item_name] = {'count': count, 'durability': None}
            target_player.db.execute(
                "INSERT INTO items (qq_id, item_id, count) VALUES (?, ?, ?)",
                (target_player.qq_id, item_name, count)
            )

        return f"你成功赠送了 {count} 个 {item_name} 给 {target_player.name}"
    
    def calculate_power(self):
        """计算玩家的实力"""
        realm_list = self.get_current_realm_list()
        realm_index = realm_list.index(self.realm)
        stage_index = self.STAGES.index(self.stage)
        cultivation_progress = self.get_cultivation_progress()
        power = realm_index * 1000 + stage_index * 100 + cultivation_progress
        return power
    
    def get_current_realm_list(self):
        """获取当前阵营的境界列表"""
        return self.REALMS.get(self.faction, [])
    
    def choose_faction(self, faction: str) -> str:
        """选择阵营"""
        if faction not in self.REALMS:
            return f"无效的阵营选择，可选阵营有: {', '.join(self.REALMS.keys())}"
        if self.faction == faction:
            return f"你已经属于 {faction} 阵营，无需重复选择。"
        self.faction = faction
        self.update()
        return f"你成功加入了 {faction} 阵营！"


    def close(self):
        self.db.close()