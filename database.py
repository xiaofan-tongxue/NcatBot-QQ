import sqlite3
from typing import List, Dict, Any
import json

class Database:
    REALMS = [
        '炼体境', '蚀骨境', 
        '练气境', '聚煞境',
        '筑基境', '铸魔台',
        '金丹境', '结魔丹',
        '元婴境', '化魔胎',
        '化神境', '炼狱境',
        '渡劫境', '逆天境',
        '大乘境', '灭世境'
    ]
    REALM_ORDER = {
    '炼体境': 1, '蚀骨境': 1,
    '练气境': 2, '聚煞境': 2,
    '筑基境': 3, '铸魔台': 3,
    '金丹境': 4, '结魔丹': 4,
    '元婴境': 5, '化魔胎': 5,
    '化神境': 6, '炼狱境': 6,
    '渡劫境': 7, '逆天境': 7,
    '大乘境': 8, '灭世境': 8
    }
    
    STAGES = ['初期', '中期', '后期', '大圆满']
    
    def __init__(self, db_file="xiuxian.db"):
        self.conn = sqlite3.connect(db_file)
        self.create_tables()
        self.initialize_data()
        
    def create_tables(self):
        cursor = self.conn.cursor()

        # 玩家基础表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            qq_id TEXT PRIMARY KEY,
            name TEXT,
            qq_nickname TEXT,
            faction TEXT CHECK(faction IN ('仙域', '魔渊', '中立')),
            realm TEXT,
            stage TEXT CHECK(stage IN ('初期', '中期', '后期', '大圆满')),
            cultivation REAL DEFAULT 0,
            health INTEGER DEFAULT 100,
            max_health INTEGER DEFAULT 100,
            mana INTEGER DEFAULT 100,
            max_mana INTEGER DEFAULT 100,
            attack INTEGER DEFAULT 10,
            defense INTEGER DEFAULT 5,
            speed INTEGER DEFAULT 5,
            gold INTEGER DEFAULT 100,
            create_time TEXT,
            last_active TEXT,
            last_cultivate TEXT,
            last_battle TEXT,
            is_cultivating BOOLEAN DEFAULT FALSE,
            cultivate_start_time TEXT,
            daily_cultivate_count INTEGER DEFAULT 0,
            last_breakthrough_attempt TEXT
        )
        ''')
        
        # 灵根表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS spiritual_roots (
            qq_id TEXT,
            root_type TEXT CHECK(root_type IN ('金', '木', '水', '火', '土', '混沌', '噬魔')),
            purity REAL CHECK(purity >= 1 AND purity <= 100),
            PRIMARY KEY (qq_id, root_type),
            FOREIGN KEY (qq_id) REFERENCES players(qq_id)
        )
        ''')
        
        # 物品表（包含配方）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            qq_id TEXT,
            item_id TEXT,
            count INTEGER DEFAULT 1,
            durability INTEGER,
            is_recipe BOOLEAN DEFAULT FALSE,
            recipe_type TEXT,
            PRIMARY KEY (qq_id, item_id),
            FOREIGN KEY (qq_id) REFERENCES players(qq_id)
        )
        ''')
        
        # 玩家已学配方表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_recipes (
            qq_id TEXT,
            recipe_type TEXT CHECK(recipe_type IN ('alchemy', 'forging', 'talisman')),
            recipe_id TEXT,
            PRIMARY KEY (qq_id, recipe_type, recipe_id),
            FOREIGN KEY (qq_id) REFERENCES players(qq_id)
        )
        ''')
        
        # 炼丹配方表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alchemy_recipes (
            recipe_id TEXT PRIMARY KEY,
            name TEXT,
            grade TEXT CHECK(grade IN ('凡品', '灵品', '仙品', '神品')),
            sub_grade TEXT CHECK(sub_grade IN ('下', '中', '上', '极品')),
            required_level INTEGER,
            ingredients TEXT,
            effect TEXT,
            is_breakthrough BOOLEAN DEFAULT FALSE
        )
        ''')
        
        # 炼器配方表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS forging_recipes (
            recipe_id TEXT PRIMARY KEY,
            name TEXT,
            type TEXT CHECK(type IN ('武器', '防具', '饰品', '法宝')),
            grade TEXT CHECK(grade IN ('法器', '灵器', '法宝', '灵宝', '仙器', '神器')),
            sub_grade TEXT CHECK(sub_grade IN ('下', '中', '上', '极品')),
            required_level INTEGER,
            materials TEXT,
            attributes TEXT
        )
        ''')
        
        # 符箓配方表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS talisman_recipes (
            recipe_id TEXT PRIMARY KEY,
            name TEXT,
            grade TEXT CHECK(grade IN ('黄符', '朱砂符', '玉符', '血骨符')),
            effect_type TEXT CHECK(effect_type IN ('攻击', '防御', '辅助', '特殊')),
            required_level INTEGER,
            materials TEXT,
            effect TEXT
        )
        ''')
        
        # 灵植表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS plants (
            plant_id TEXT PRIMARY KEY,
            name TEXT,
            growth_stages INTEGER,
            required_environment TEXT,
            yield_items TEXT,
            variant_chance REAL
        )
        ''')
        
        # 玩家灵田表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_farms (
            qq_id TEXT,
            plot_id INTEGER,
            plant_id TEXT,
            growth_stage INTEGER DEFAULT 0,
            growth_time TEXT,
            is_variant BOOLEAN DEFAULT FALSE,
            PRIMARY KEY (qq_id, plot_id),
            FOREIGN KEY (qq_id) REFERENCES players(qq_id)
        )
        ''')
        
        # 势力声望表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS faction_reputation (
            qq_id TEXT,
            faction TEXT,
            reputation INTEGER DEFAULT 0,
            contribution INTEGER DEFAULT 0,
            rank INTEGER DEFAULT 0,
            PRIMARY KEY (qq_id, faction),
            FOREIGN KEY (qq_id) REFERENCES players(qq_id)
        )
        ''')
        
        # 任务表（新增任务等级和奖励类型）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS quests (
            quest_id TEXT PRIMARY KEY,
            name TEXT,
            type TEXT CHECK(type IN ('主线', '支线', '日常', '副本')),
            level TEXT CHECK(level IN ('下等', '中等', '上等')),
            required_realm TEXT,
            required_faction TEXT,
            objectives TEXT,
            rewards TEXT,
            reward_type TEXT CHECK(reward_type IN ('alchemy', 'forging', 'talisman', 'item')),
            is_repeatable BOOLEAN
        )
        ''')
        
        # 活跃任务表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_quests (
            quest_id TEXT,
            qq_id TEXT,
            expire_time TEXT,
            PRIMARY KEY (quest_id, qq_id),
            FOREIGN KEY (quest_id) REFERENCES quests(quest_id),
            FOREIGN KEY (qq_id) REFERENCES players(qq_id)
        )
        ''')
        
        # 战斗记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS battle_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            qq_id TEXT,
            opponent_id TEXT,
            result TEXT,
            details TEXT,
            battle_time TEXT,
            FOREIGN KEY (qq_id) REFERENCES players(qq_id)
        )
        ''')
        
        # 妖兽表（新增等级和掉落物品）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS monsters (
            monster_id TEXT PRIMARY KEY,
            name TEXT,
            level TEXT CHECK(level IN ('low', 'medium', 'high')),
            health INTEGER,
            attack INTEGER,
            defense INTEGER,
            drop_items TEXT,
            realm_requirement TEXT
        )
        ''')
        
        # 材料来源表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS material_sources (
            material_id TEXT PRIMARY KEY,
            name TEXT,
            source_type TEXT CHECK(source_type IN ('monster', 'quest', 'farm')),
            source_level TEXT CHECK(source_level IN ('low', 'medium', 'high')),
            drop_rate REAL
        )
        ''')
        
        self.conn.commit()
        
    def initialize_data(self):
        """初始化游戏基础数据"""
        # 检查是否已经初始化过
        if self.fetch_one("SELECT 1 FROM alchemy_recipes LIMIT 1"):
            return
            
        # 初始化突破丹药配方
        breakthrough_pills = [
            {'recipe_id': 'pill_base', 'name': '筑基丹', 'grade': '凡品', 'sub_grade': '下', 
             'required_level': 1, 'ingredients': {'灵草': 2, '裂海玄龟核': 1}, 
             'effect': '突破至炼体境必备丹药', 'is_breakthrough': True},
            {'recipe_id': 'pill_shagu', 'name': '聚煞丹', 'grade': '凡品', 'sub_grade': '下', 
             'required_level': 2, 'ingredients': {'魔草': 2, '腐骨核': 1}, 
             'effect': '突破至蚀骨境必备丹药', 'is_breakthrough': True},
            {'recipe_id': 'pill_base', 'name': '凝气丹', 'grade': '灵品', 'sub_grade': '中', 
             'required_level': 1, 'ingredients': {'灵草': 5, '裂海玄龟核': 2,'碧眼灵猴核': 1}, 
             'effect': '突破至练气境必备丹药', 'is_breakthrough': True},
            {'recipe_id': 'pill_shagu', 'name': '魔煞丹', 'grade': '灵品', 'sub_grade': '中', 
             'required_level': 2, 'ingredients': {'魔草': 5, '腐骨核': 2,'噬魂核': 1}, 
             'effect': '突破至聚煞境必备丹药', 'is_breakthrough': True},
            {'recipe_id': 'pill_shagu', 'name': '金丹', 'grade': '灵品', 'sub_grade': '上', 
             'required_level': 2, 'ingredients': {'灵草': 10, '碧眼灵猴核': 5,'乙木灵藤核': 3}, 
             'effect': '突破至筑基境必备丹药', 'is_breakthrough': True},
            {'recipe_id': 'pill_shagu', 'name': '魔心丹', 'grade': '灵品', 'sub_grade': '上', 
             'required_level': 2, 'ingredients': {'魔草': 10, '噬魂核': 5,'熔魔核': 3}, 
             'effect': '突破至铸魔台必备丹药', 'is_breakthrough': True},
            {'recipe_id': 'pill_shagu', 'name': '元婴丹', 'grade': '仙品', 'sub_grade': '中', 
             'required_level': 2, 'ingredients': {'灵草': 50, '乙木灵藤核': 5,'庚金铁翼核': 4}, 
             'effect': '突破至金丹境必备丹药', 'is_breakthrough': True},
            {'recipe_id': 'pill_shagu', 'name': '化魔丹', 'grade': '仙品', 'sub_grade': '中', 
             'required_level': 2, 'ingredients': {'魔草': 50, '熔魔核': 5,'骨龙核': 4}, 
             'effect': '突破至结魔丹必备丹药', 'is_breakthrough': True},
            {'recipe_id': 'pill_shagu', 'name': '化神丹', 'grade': '仙品', 'sub_grade': '上', 
             'required_level': 2, 'ingredients': {'灵草': 100, '庚金铁翼核': 8,'雷狱麒麟核': 4}, 
             'effect': '突破至元婴境必备丹药', 'is_breakthrough': True},
            {'recipe_id': 'pill_shagu', 'name': '炼狱丹', 'grade': '仙品', 'sub_grade': '上', 
             'required_level': 2, 'ingredients': {'魔草': 100, '骨龙核': 8,'万蛊核': 4}, 
             'effect': '突破至化魔胎必备丹药', 'is_breakthrough': True},
            {'recipe_id': 'pill_shagu', 'name': '渡劫丹', 'grade': '仙品', 'sub_grade': '极品', 
             'required_level': 2, 'ingredients': {'灵草': 200, '雷狱麒麟核': 2,'离火玄鸟核': 2}, 
             'effect': '突破至化神境必备丹药', 'is_breakthrough': True},
            {'recipe_id': 'pill_shagu', 'name': '逆天丹', 'grade': '仙品', 'sub_grade': '极品', 
             'required_level': 2, 'ingredients': {'魔草': 200, '万蛊核': 2,'炎魔核': 2}, 
             'effect': '突破至炼狱境必备丹药', 'is_breakthrough': True},
            {'recipe_id': 'pill_shagu', 'name': '大乘丹', 'grade': '神品', 'sub_grade': '极品', 
             'required_level': 2, 'ingredients': {'灵草': 400, '雷狱麒麟核': 4,'离火玄鸟核': 5}, 
             'effect': '突破至渡劫境必备丹药', 'is_breakthrough': True},
            {'recipe_id': 'pill_shagu', 'name': '灭世丹', 'grade': '神品', 'sub_grade': '极品', 
             'required_level': 2, 'ingredients': {'魔草': 400, '万蛊核': 4,'炎魔核': 5}, 
             'effect': '突破至逆天境必备丹药', 'is_breakthrough': True}
            # ...其他突破丹药...
        ]
        
        # 初始化普通丹药配方
        normal_pills = [
            {'recipe_id': 'pill_1', 'name': '气血丹', 'grade': '凡品', 'sub_grade': '中',
             'required_level': 1, 'ingredients': {'灵草': 2,"气血草" : 2}, 'effect': '恢复10点气血(不超过血量上限)'},
            {'recipe_id': 'pill_2', 'name': '九转续命丹', 'grade': '灵品', 'sub_grade': '中',
             'required_level': 1, 'ingredients': {'碧眼灵猴核': 1,"气血草" : 3}, 'effect': '提升10点气血上限'},
            {'recipe_id': 'pill_3', 'name': '紫府固元丹', 'grade': '仙品', 'sub_grade': '上',
             'required_level': 1, 'ingredients': {'气血草': 2,"玄黄参" : 2,"碧眼灵猴核": 2, "乙木灵藤核" : 1}, 'effect': '提升气血上限5%'},
            {'recipe_id': 'pill_4', 'name': '天罡护体丹', 'grade': '仙品', 'sub_grade': '上',
             'required_level': 1, 'ingredients': {'鸿蒙青莲子': 2,"星辰藤" : 2,"碧眼灵猴核": 2, "乙木灵藤核" : 1}, 'effect': '提升7%防御上限'},
            {'recipe_id': 'pill_5', 'name': '太虚破魔丹', 'grade': '仙品', 'sub_grade': '上',
             'required_level': 1, 'ingredients': {'紫霄神雷竹': 2,"太虚仙芝" : 2,"碧眼灵猴核": 2, "乙木灵藤核" : 1}, 'effect': '提升7%攻击强度'},
            {'recipe_id': 'pill_6', 'name': '魔血丹', 'grade': '凡品', 'sub_grade': '中',
             'required_level': 1, 'ingredients': {'魔草': 2,"嗜血草" : 2}, 'effect': '恢复10点气血(不超过血量上限)'},
            {'recipe_id': 'pill_2', 'name': '蚀骨再生丹', 'grade': '灵品', 'sub_grade': '中',
             'required_level': 1, 'ingredients': {'蚀骨幽莲': 1,"嗜血草" : 3}, 'effect': '提升10点气血上限'},
            {'recipe_id': 'pill_3', 'name': '魔胎吞天丹', 'grade': '仙品', 'sub_grade': '上',
             'required_level': 1, 'ingredients': {'嗜血草': 2,"蚀骨幽莲" : 2,"噬魂核": 2, "熔魔核" : 1}, 'effect': '提升气血上限5%'},
            {'recipe_id': 'pill_4', 'name': '冥河护盾丹', 'grade': '仙品', 'sub_grade': '上',
             'required_level': 1, 'ingredients': {'九幽冥河草': 2,"煞血藤" : 2,"噬魂核": 2, "熔魔核" : 1}, 'effect': '提升7%防御上限'},
            {'recipe_id': 'pill_5', 'name': '灭世魔焰丹', 'grade': '仙品', 'sub_grade': '上',
             'required_level': 1, 'ingredients': {'灭世黑莲': 2,"万魔血晶花" : 2,"噬魂核": 2, "熔魔核" : 1}, 'effect': '提升7%攻击强度'},
            # ...其他普通丹药...
        ]

        # 初始化炼器配方
        forging_recipes = [
             # ------------------- 仙器 -------------------
             # ------------------- 灵器等级 -------------------
            # ------------------- 凡品（法器） -------------------
            {
                'recipe_id': 'sword_1', 
                'name': '裂海青纹剑', 
                'type': '武器',
                'grade': '凡品',
                'required_level': 1, 
                'materials': {'裂海玄龟核': 2, '青纹铁': 3},
                'attributes': {'攻击': 15}
            },
            {
                'recipe_id': 'armor_1', 
                'name': '灵猴赤精甲', 
                'type': '防具',
                'grade': '凡品',
                'required_level': 1, 
                'materials': {'碧眼灵猴核': 2, '赤精铁': 3},
                'attributes': {'防御': 12}
            },
            
            # ------------------- 灵品（灵器） -------------------
            {
                'recipe_id': 'sword_2', 
                'name': '乙木寒纹刀', 
                'type': '武器',
                'grade': '灵品',
                'required_level': 3, 
                'materials': {'乙木灵藤核': 2, '寒纹铁': 3},
                'attributes': {'攻击': 28}
            },
            {
                'recipe_id': 'armor_2', 
                'name': '庚金玄墨铠', 
                'type': '防具',
                'grade': '灵品',
                'required_level': 3, 
                'materials': {'庚金铁翼核': 2, '玄墨铁': 3},
                'attributes': {'防御': 22}
            },
            
            # ------------------- 仙品（法宝） -------------------
            {
                'recipe_id': 'sword_3', 
                'name': '麒麟星辰枪', 
                'type': '武器',
                'grade': '仙品',
                'required_level': 5, 
                'materials': {'雷狱麒麟核': 2, '星辰铁': 3},
                'attributes': {'攻击': 45}
            },
            {
                'recipe_id': 'armor_3', 
                'name': '鲲鹏鸿蒙袍', 
                'type': '防具',
                'grade': '仙品',
                'required_level': 5, 
                'materials': {'玄冰鲲鹏核': 2, '鸿蒙玄铁': 3},
                'attributes': {'防御': 35}
            },
            
            # ------------------- 神品（灵宝） -------------------
            {
                'recipe_id': 'sword_4', 
                'name': '玄鸟阴阳刃', 
                'type': '武器',
                'grade': '神品',
                'required_level': 7, 
                'materials': {'离火玄鸟核': 2, '太极阴阳铁': 3},
                'attributes': {'攻击': 65}
            },
            {
                'recipe_id': 'armor_4', 
                'name': '龙祖灭世甲', 
                'type': '防具',
                'grade': '神品',
                'required_level': 7, 
                'materials': {'龙核': 2, '灭世陨铁': 3},
                'attributes': {'防御': 50}
            },
            # ------------------- 饰品（凡品-神品） -------------------
            {
                'recipe_id': 'ring_1', 
                'name': '玄龟青纹戒', 
                'type': '饰品',
                'grade': '凡品',
                'required_level': 1, 
                'materials': {'裂海玄龟核': 1, '青纹铁': 2},
                'attributes': {'攻击': 5, '防御': 3}
            },
            {
                'recipe_id': 'ring_2', 
                'name': '灵猴赤精环', 
                'type': '饰品',
                'grade': '灵品',
                'required_level': 3, 
                'materials': {'碧眼灵猴核': 1, '赤精铁': 2},
                'attributes': {'攻击': 8, '防御': 5, '气血': 30}
            },
            {
                'recipe_id': 'ring_3', 
                'name': '麒麟星辰佩', 
                'type': '饰品',
                'grade': '仙品',
                'required_level': 5, 
                'materials': {'雷狱麒麟核': 1, '星辰铁': 2},
                'attributes': {'攻击': 12, '防御': 8, '气血': 60}
            },
            {
                'recipe_id': 'ring_4', 
                'name': '龙祖灭世坠', 
                'type': '饰品',
                'grade': '神品',
                'required_level': 7, 
                'materials': {'龙核': 1, '灭世陨铁': 2},
                'attributes': {'攻击': 18, '防御': 12, '气血': 100}
            },
            
            # ------------------- 法宝（凡品-神品） -------------------
            {
                'recipe_id': 'treasure_1', 
                'name': '玄龟青纹盾', 
                'type': '法宝',
                'grade': '凡品',
                'required_level': 1, 
                'materials': {'裂海玄龟核': 3, '青纹铁': 5},
                'attributes': {'防御': 8, '气血': 80}
            },
            {
                'recipe_id': 'treasure_2', 
                'name': '乙木寒纹灯', 
                'type': '法宝',
                'grade': '灵品',
                'required_level': 3, 
                'materials': {'乙木灵藤核': 3, '寒纹铁': 5},
                'attributes': {'攻击': 15, '防御': 10}
            },
            {
                'recipe_id': 'treasure_3', 
                'name': '鲲鹏鸿蒙镜', 
                'type': '法宝',
                'grade': '仙品',
                'required_level': 5, 
                'materials': {'玄冰鲲鹏核': 3, '鸿蒙玄铁': 5},
                'attributes': {'攻击': 22, '防御': 15, '气血': 150}
            },
            {
                'recipe_id': 'treasure_4', 
                'name': '玄鸟阴阳幡', 
                'type': '法宝',
                'grade': '神品',
                'required_level': 7, 
                'materials': {'离火玄鸟核': 3, '太极阴阳铁': 5},
                'attributes': {'攻击': 30, '防御': 20, '气血': 200}
            },
            # ------------------- 魔兵等级 -------------------
            # ------------------- 凡品（法器） -------------------
            {
                'recipe_id': 'demon_sword_1', 
                'name': '腐骨蚀铁刃', 
                'type': '武器',
                'grade': '凡品',
                'required_level': 1, 
                'materials': {'腐骨核': 2, '蚀骨铁屑': 3},
                'attributes': {'攻击': 18}
            },
            {
                'recipe_id': 'demon_armor_1', 
                'name': '噬魂聚晶甲', 
                'type': '防具',
                'grade': '凡品',
                'required_level': 1, 
                'materials': {'噬魂核': 2, '聚煞赤晶': 3},
                'attributes': {'防御': 15, '气血': 60}
            },
            
            # ------------------- 灵品（灵器） -------------------
            {
                'recipe_id': 'demon_sword_2', 
                'name': '熔魔铸魔刀', 
                'type': '武器',
                'grade': '灵品',
                'required_level': 3, 
                'materials': {'熔魔核': 2, '铸魔黑铁': 3},
                'attributes': {'攻击': 32}
            },
            {
                'recipe_id': 'demon_armor_2', 
                'name': '骨龙魔丹铠', 
                'type': '防具',
                'grade': '灵品',
                'required_level': 3, 
                'materials': {'骨龙核': 2, '魔丹碎晶': 3},
                'attributes': {'防御': 25, '气血': 120}
            },
            
            # ------------------- 仙品（法宝） -------------------
            {
                'recipe_id': 'demon_sword_3', 
                'name': '万蛊化魔枪', 
                'type': '武器',
                'grade': '仙品',
                'required_level': 5, 
                'materials': {'万蛊核': 2, '化魔胎砂': 3},
                'attributes': {'攻击': 48}
            },
            {
                'recipe_id': 'demon_armor_3', 
                'name': '炎魔炼狱袍', 
                'type': '防具',
                'grade': '仙品',
                'required_level': 5, 
                'materials': {'炎魔核': 2, '炼狱焦铁': 3},
                'attributes': {'防御': 38, '气血': 200}
            },
            
            # ------------------- 神品（灵宝） -------------------
            {
                'recipe_id': 'demon_sword_4', 
                'name': '心魔逆天刃', 
                'type': '武器',
                'grade': '神品',
                'required_level': 7, 
                'materials': {'心魔核': 2, '逆天魔晶': 3},
                'attributes': {'攻击': 70}
            },
            {
                'recipe_id': 'demon_armor_4', 
                'name': '灭世龙陨甲', 
                'type': '防具',
                'grade': '神品',
                'required_level': 7, 
                'materials': {'灭世龙核': 2, '灭世陨铁': 3},
                'attributes': {'防御': 55, '气血': 300}
            },
            {
                'recipe_id': 'demon_ring_1', 
                'name': '腐骨蚀铁戒', 
                'type': '饰品',
                'grade': '凡品',
                'required_level': 1, 
                'materials': {'腐骨核': 1, '蚀骨铁屑': 2},
                'attributes': {'攻击': 6, '防御': 4}
            },
            {
                'recipe_id': 'demon_ring_2', 
                'name': '噬魂聚晶环', 
                'type': '饰品',
                'grade': '灵品',
                'required_level': 3, 
                'materials': {'噬魂核': 1, '聚煞赤晶': 2},
                'attributes': {'攻击': 9, '防御': 6, '气血': 40}
            },
            {
                'recipe_id': 'demon_ring_3', 
                'name': '炎魔炼狱佩', 
                'type': '饰品',
                'grade': '仙品',
                'required_level': 5, 
                'materials': {'炎魔核': 1, '炼狱焦铁': 2},
                'attributes': {'攻击': 13, '防御': 9, '气血': 70}
            },
            {
                'recipe_id': 'demon_ring_4', 
                'name': '灭世龙陨坠', 
                'type': '饰品',
                'grade': '神品',
                'required_level': 7, 
                'materials': {'灭世龙核': 1, '灭世陨铁': 2},
                'attributes': {'攻击': 20, '防御': 13, '气血': 120}
            },
            
            # ------------------- 法宝（凡品-神品） -------------------
            {
                'recipe_id': 'demon_treasure_1', 
                'name': '腐骨蚀铁盾', 
                'type': '法宝',
                'grade': '凡品',
                'required_level': 1, 
                'materials': {'腐骨核': 3, '蚀骨铁屑': 5},
                'attributes': {'防御': 10, '气血': 100}
            },
            {
                'recipe_id': 'demon_treasure_2', 
                'name': '熔魔铸魔鼎', 
                'type': '法宝',
                'grade': '灵品',
                'required_level': 3, 
                'materials': {'熔魔核': 3, '铸魔黑铁': 5},
                'attributes': {'攻击': 18, '防御': 12}
            },
            {
                'recipe_id': 'demon_treasure_3', 
                'name': '万蛊化魔幡', 
                'type': '法宝',
                'grade': '仙品',
                'required_level': 5, 
                'materials': {'万蛊核': 3, '化魔胎砂': 5},
                'attributes': {'攻击': 25, '防御': 18, '气血': 180}
            },
            {
                'recipe_id': 'demon_treasure_4', 
                'name': '心魔逆天钟', 
                'type': '法宝',
                'grade': '神品',
                'required_level': 7, 
                'materials': {'心魔核': 3, '逆天魔晶': 5},
                'attributes': {'攻击': 35, '防御': 25, '气血': 250}
            }
            # ...其他炼器配方...
        ]
        
        # 初始化符箓配方
        talisman_recipes = [
            # ------------------- 仙域  -------------------
            # ------------------- 黄符（凡品） -------------------
            {
                'recipe_id': 'talisman_fire_1', 
                'name': '裂海玄龟符', 
                'grade': '黄符',
                'effect_type': '攻击', 
                'required_level': 1, 
                'materials': {'裂海玄龟核': 1, '青纹铁': 1},
                'effect': '对目标造成[攻击*0.8]点水属性伤害'
            },
            {
                'recipe_id': 'talisman_shield_1', 
                'name': '碧眼灵猴符', 
                'grade': '黄符',
                'effect_type': '防御', 
                'required_level': 1, 
                'materials': {'碧眼灵猴核': 1, '赤精铁': 1},
                'effect': '生成护盾，吸收[防御*2]点伤害，持续1回合'
            },
            
            # ------------------- 朱砂符（灵品） -------------------
            {
                'recipe_id': 'talisman_lightning_1', 
                'name': '乙木灵藤符', 
                'grade': '朱砂符',
                'effect_type': '攻击', 
                'required_level': 3, 
                'materials': {'乙木灵藤核': 1, '寒纹铁': 1},
                'effect': '对目标造成[攻击*1.2]点木属性伤害，有20%概率降低其10%攻击，持续2回合'
            },
            {
                'recipe_id': 'talisman_heal_1', 
                'name': '庚金铁翼符', 
                'grade': '朱砂符',
                'effect_type': '辅助', 
                'required_level': 3, 
                'materials': {'庚金铁翼核': 1, '玄墨铁': 1},
                'effect': '恢复[最大生命值*15%]点生命，并提升5%防御，持续3回合'
            },
            
            # ------------------- 玉符（仙品） -------------------
            {
                'recipe_id': 'talisman_firestorm_1', 
                'name': '雷狱麒麟符', 
                'grade': '玉符',
                'effect_type': '攻击', 
                'required_level': 5, 
                'materials': {'雷狱麒麟核': 1, '星辰铁': 1},
                'effect': '对全体敌人造成[攻击*0.9]点雷属性伤害，有30%概率麻痹目标1回合'
            },
            {
                'recipe_id': 'talisman_barrier_1', 
                'name': '玄冰鲲鹏符', 
                'grade': '玉符',
                'effect_type': '防御', 
                'required_level': 5, 
                'materials': {'玄冰鲲鹏核': 1, '鸿蒙玄铁': 1},
                'effect': '全体获得护盾，吸收[防御*3]点伤害，并免疫下一次控制效果'
            },
            
            # ------------------- 血骨符（高阶） -------------------
            {
                'recipe_id': 'talisman_dragon_1', 
                'name': '离火玄鸟符', 
                'grade': '血骨符',
                'effect_type': '特殊', 
                'required_level': 7, 
                'materials': {'离火玄鸟核': 1, '太极阴阳铁': 1},
                'effect': '无视目标30%防御，造成[攻击*1.5]点火属性伤害，使用后进入2回合冷却'
            },
            {
                'recipe_id': 'talisman_teleport_1', 
                'name': '创世龙祖符', 
                'grade': '血骨符',
                'effect_type': '特殊', 
                'required_level': 7, 
                'materials': {'龙核': 1, '灭世陨铁': 1},
                'effect': '立即结束当前战斗并传送至安全区，携带的物品掉落概率降低50%'
            },
            # ------------------- 魔渊 -------------------
            # ------------------- 黄符（凡品） -------------------
            {
                'recipe_id': 'demon_talisman_poison_1', 
                'name': '腐骨血蛭符', 
                'grade': '黄符',
                'effect_type': '攻击', 
                'required_level': 1, 
                'materials': {'腐骨核': 1, '蚀骨铁屑': 1},
                'effect': '对目标造成[攻击*0.7]点毒属性伤害，每秒额外损失5点生命，持续2回合'
            },
            {
                'recipe_id': 'demon_talisman_weakness_1', 
                'name': '噬魂夜枭符', 
                'grade': '黄符',
                'effect_type': '辅助', 
                'required_level': 1, 
                'materials': {'噬魂核': 1, '聚煞赤晶': 1},
                'effect': '降低目标15%防御，持续3回合，同时提升自身5%攻击'
            },
            
            # ------------------- 朱砂符（灵品） -------------------
            {
                'recipe_id': 'demon_talisman_burn_1', 
                'name': '熔浆魔蛛符', 
                'grade': '朱砂符',
                'effect_type': '攻击', 
                'required_level': 3, 
                'materials': {'熔魔核': 1, '铸魔黑铁': 1},
                'effect': '对目标造成[攻击*1.1]点火属性伤害，并有40%概率使其陷入灼烧状态，持续3回合'
            },
            {
                'recipe_id': 'demon_talisman_heal_1', 
                'name': '冥河骨龙符', 
                'grade': '朱砂符',
                'effect_type': '辅助', 
                'required_level': 3, 
                'materials': {'骨龙核': 1, '魔丹碎晶': 1},
                'effect': '吸取目标[攻击*0.8]点生命转化为自身生命，并提升10%吸血效果，持续2回合'
            },
            
            # ------------------- 玉符（仙品） -------------------
            {
                'recipe_id': 'demon_talisman_swarm_1', 
                'name': '万蛊母虫符', 
                'grade': '玉符',
                'effect_type': '攻击', 
                'required_level': 5, 
                'materials': {'万蛊核': 1, '化魔胎砂': 1},
                'effect': '对全体敌人造成[攻击*0.85]点毒属性伤害，有50%概率附加中毒状态，持续3回合'
            },
            {
                'recipe_id': 'demon_talisman_armor_1', 
                'name': '灭世炎魔符', 
                'grade': '玉符',
                'effect_type': '防御', 
                'required_level': 5, 
                'materials': {'炎魔核': 1, '炼狱焦铁': 1},
                'effect': '全体获得护盾，吸收[防御*2.5]点伤害，并反弹15%的物理伤害，持续2回合'
            },
            
            # ------------------- 血骨符（高阶） -------------------
            {
                'recipe_id': 'demon_talisman_mind_1', 
                'name': '混沌心魔符', 
                'grade': '血骨符',
                'effect_type': '特殊', 
                'required_level': 7, 
                'materials': {'心魔核': 1, '逆天魔晶': 1},
                'effect': '使目标陷入混乱状态，持续2回合（攻击敌我不分），对精神力低于自身的目标必定生效'
            },
            {
                'recipe_id': 'demon_talisman_destruction_1', 
                'name': '原初灭世龙符', 
                'grade': '血骨符',
                'effect_type': '攻击', 
                'required_level': 7, 
                'materials': {'灭世龙核': 1, '灭世陨铁': 1},
                'effect': '对目标造成[攻击*1.8]点毁灭伤害，有25%概率直接斩杀生命值低于30%的敌人'
            }
            # ...其他符箓配方...
        ]
        
        # 初始化妖兽数据
        monsters = [
            {'monster_id': 'monster_1', 'name': '裂海玄龟', 'level': 'low',
             'health': 50, 'attack': 10, 'defense': 5, 
             'drop_items': '{"裂海玄龟核": 0.3, "青纹铁": 0.8,"玄龟涎膜":0.2}',
             'realm_requirement': '炼体境'},
            {'monster_id': 'monster_2', 'name': '碧眼灵猴', 'level': 'medium',
             'health': 100, 'attack': 20, 'defense': 10,
             'drop_items': '{"碧眼灵猴核": 0.6, "赤精铁": 0.5,"灵猴眉心毫":0.2}',
             'realm_requirement': '练气境'},
            {'monster_id': 'monster_3', 'name': '乙木灵藤', 'level': 'high',
             'health': 200, 'attack': 40, 'defense': 20,
             'drop_items': '{"乙木灵藤核": 0.8, "寒纹铁": 0.3,"灵藤心髓":0.2}',
             'realm_requirement': '筑基境'},
            {'monster_id': 'monster_4', 'name': '庚金铁翼', 'level': 'high',
             'health': 300, 'attack': 80, 'defense': 30,
             'drop_items': '{"庚金铁翼核": 0.8, "玄墨铁": 0.3,"铁翼翎羽":0.2}',
             'realm_requirement': '金丹境'},
            {'monster_id': 'monster_5', 'name': '雷狱麒麟', 'level': 'low',
             'health': 400, 'attack': 100, 'defense': 40, 
             'drop_items': '{"雷狱麒麟核": 0.3, "星辰铁": 0.8,"麒麟雷毛":0.2}',
             'realm_requirement': '元婴境'},
            {'monster_id': 'monster_6', 'name': '玄冰鲲鹏', 'level': 'medium',
             'health': 500, 'attack': 120, 'defense': 50,
             'drop_items': '{"玄冰鲲鹏核": 0.6, "鸿蒙玄铁": 0.5,"鲲鹏喉骨":0.2}',
             'realm_requirement': '化神境'},
            {'monster_id': 'monster_7', 'name': '离火玄鸟', 'level': 'high',
             'health': 600, 'attack': 140, 'defense': 60,
             'drop_items': '{"离火玄鸟核": 0.8, "太极阴阳铁": 0.3,"玄鸟尾羽":0.2}',
             'realm_requirement': '渡劫境'},
            {'monster_id': 'monster_8', 'name': '创世龙祖敖玄', 'level': 'high',
             'health': 700, 'attack': 40, 'defense': 70,
             'drop_items': '{"龙核": 0.8, "灭世陨铁": 0.3,"龙祖鳞粉":0.2}',
             'realm_requirement': '大乘境'},
            {'monster_id': 'monster_9','name': '腐骨血蛭', 'level': 'low',
            'health': 50, 'attack': 10, 'defense': 5, 
            'drop_items': '{"腐骨核": 0.3, "蚀骨铁屑": 0.8, "血蛭涎液": 0.2}',
            'realm_requirement': '蚀骨境'},
            {'monster_id': 'monster_10','name': '噬魂夜枭','level': 'medium',
            'health': 100, 'attack': 20,'defense': 10, 
            'drop_items': '{"噬魂核": 0.6, "聚煞赤晶": 0.5, "夜枭魂羽": 0.2}',
            'realm_requirement': '聚煞境'},
            {'monster_id': 'monster_11', 'name': '熔浆魔蛛', 'level': 'high',
            'health': 200, 'attack': 40, 'defense': 20, 
            'drop_items': '{"熔魔核": 0.8, "铸魔黑铁": 0.3, "魔蛛火丝": 0.2}',
            'realm_requirement': '铸魔台'},
            {'monster_id': 'monster_12','name': '冥河骨龙', 'level': 'high',
            'health': 300, 'attack': 40, 'defense': 20, 
            'drop_items': '{"骨龙核": 0.8, "魔丹碎晶": 0.3, "骨龙脊骨": 0.2}',
            'realm_requirement': '结魔丹'},
            {'monster_id': 'monster_13', 'name': '万蛊母虫', 'level': 'low',
            'health': 400, 'attack': 10, 'defense': 5, 
            'drop_items': '{"万蛊核": 0.3, "化魔胎砂": 0.8, "母虫涎腺": 0.2}',
            'realm_requirement': '化魔胎'},
            {'monster_id': 'monster_14','name': '灭世炎魔','level': 'medium',
            'health': 500, 'attack': 20, 'defense': 10, 
            'drop_items': '{"炎魔核": 0.6, "炼狱焦铁": 0.5, "炎魔心血": 0.2}',
            'realm_requirement': '炼狱境'},
            {'monster_id': 'monster_15', 'name': '混沌心魔', 'level': 'high',
            'health': 600, 'attack': 40, 'defense': 20, 
            'drop_items': '{"心魔核": 0.8, "逆天魔晶": 0.3, "心魔涎液": 0.2}',
            'realm_requirement': '逆天境'},
            {'monster_id': 'monster_16', 'name': '原初灭世龙', 'level': 'high',
            'health': 700, 'attack': 40, 'defense': 20, 
            'drop_items': '{"灭世龙核": 0.8, "灭世陨铁": 0.3, "灭世龙鳞": 0.2}',
            'realm_requirement': '灭世境'}
        ]
        
        # 初始化材料来源
        materials = [
            # ------------------- 仙域材料 -------------------
            {
                'material_id': 'liehai_xuangui_he', 
                'name': '裂海玄龟核', 
                'source_type': 'monster',
                'source_level': 'low', 
                'drop_rate': 0.3
            },
            {
                'material_id': 'qingwen_tie', 
                'name': '青纹铁', 
                'source_type': 'monster',
                'source_level': 'low', 
                'drop_rate': 0.8
            },
            {
                'material_id': 'biyan_linghou_he', 
                'name': '碧眼灵猴核', 
                'source_type': 'monster',
                'source_level': 'medium', 
                'drop_rate': 0.6
            },
            {
                'material_id': 'chijing_tie', 
                'name': '赤精铁', 
                'source_type': 'monster',
                'source_level': 'medium', 
                'drop_rate': 0.5
            },
            {
                'material_id': 'yimu_lingteng_he', 
                'name': '乙木灵藤核', 
                'source_type': 'monster',
                'source_level': 'high', 
                'drop_rate': 0.8
            },
            {
                'material_id': 'hanwen_tie', 
                'name': '寒纹铁', 
                'source_type': 'monster',
                'source_level': 'high', 
                'drop_rate': 0.3
            },
            {
                'material_id': '庚金铁翼核', 
                'name': '庚金铁翼核', 
                'source_type': 'monster',
                'source_level': 'high', 
                'drop_rate': 0.8
            },
            {
                'material_id': '玄墨铁', 
                'name': '玄墨铁', 
                'source_type': 'monster',
                'source_level': 'high', 
                'drop_rate': 0.3
            },
            {
                'material_id': 'leiyu_qilin_he', 
                'name': '雷狱麒麟核', 
                'source_type': 'monster',
                'source_level': 'low', 
                'drop_rate': 0.3
            },
            {
                'material_id': 'xingchen_tie', 
                'name': '星辰铁', 
                'source_type': 'monster',
                'source_level': 'low', 
                'drop_rate': 0.8
            },
            {
                'material_id': 'xuanbing_kunpeng_he', 
                'name': '玄冰鲲鹏核', 
                'source_type': 'monster',
                'source_level': 'medium', 
                'drop_rate': 0.6
            },
            {
                'material_id': 'hongmeng_xuantie', 
                'name': '鸿蒙玄铁', 
                'source_type': 'monster',
                'source_level': 'medium', 
                'drop_rate': 0.5
            },
            {
                'material_id': 'lihuo_xuanniao_he', 
                'name': '离火玄鸟核', 
                'source_type': 'monster',
                'source_level': 'high', 
                'drop_rate': 0.8
            },
            {
                'material_id': 'taiji_yangyantie', 
                'name': '太极阴阳铁', 
                'source_type': 'monster',
                'source_level': 'high', 
                'drop_rate': 0.3
            },
            {
                'material_id': 'long_he', 
                'name': '龙核', 
                'source_type': 'monster',
                'source_level': 'high', 
                'drop_rate': 0.8
            },
            {
                'material_id': 'mieshi_yuntie', 
                'name': '灭世陨铁', 
                'source_type': 'monster',
                'source_level': 'high', 
                'drop_rate': 0.3
            },
            
            # ------------------- 魔域材料 -------------------
            {
                'material_id': 'fugu_he', 
                'name': '腐骨核', 
                'source_type': 'monster',
                'source_level': 'low', 
                'drop_rate': 0.3
            },
            {
                'material_id': 'shigu_tiexue', 
                'name': '蚀骨铁屑', 
                'source_type': 'monster',
                'source_level': 'low', 
                'drop_rate': 0.8
            },
            {
                'material_id': 'shihun_he', 
                'name': '噬魂核', 
                'source_type': 'monster',
                'source_level': 'medium', 
                'drop_rate': 0.6
            },
            {
                'material_id': 'jusha_chijing', 
                'name': '聚煞赤晶', 
                'source_type': 'monster',
                'source_level': 'medium', 
                'drop_rate': 0.5
            },
            {
                'material_id': 'rongmo_he', 
                'name': '熔魔核', 
                'source_type': 'monster',
                'source_level': 'high', 
                'drop_rate': 0.8
            },
            {
                'material_id': 'zhumo_heitie', 
                'name': '铸魔黑铁', 
                'source_type': 'monster',
                'source_level': 'high', 
                'drop_rate': 0.3
            },
            {
                'material_id': 'gulong_he', 
                'name': '骨龙核', 
                'source_type': 'monster',
                'source_level': 'high', 
                'drop_rate': 0.8
            },
            {
                'material_id': 'modan_suijing', 
                'name': '魔丹碎晶', 
                'source_type': 'monster',
                'source_level': 'high', 
                'drop_rate': 0.3
            },
            {
                'material_id': 'wangu_he', 
                'name': '万蛊核', 
                'source_type': 'monster',
                'source_level': 'low', 
                'drop_rate': 0.3
            },
            {
                'material_id': 'huamo_taisha', 
                'name': '化魔胎砂', 
                'source_type': 'monster',
                'source_level': 'low', 
                'drop_rate': 0.8
            },
            {
                'material_id': 'yanmo_he', 
                'name': '炎魔核', 
                'source_type': 'monster',
                'source_level': 'medium', 
                'drop_rate': 0.6
            },
            {
                'material_id': 'lianyu_jiaotie', 
                'name': '炼狱焦铁', 
                'source_type': 'monster',
                'source_level': 'medium', 
                'drop_rate': 0.5
            },
            {
                'material_id': 'xinmo_he', 
                'name': '心魔核', 
                'source_type': 'monster',
                'source_level': 'high', 
                'drop_rate': 0.8
            },
            {
                'material_id': 'nitian_mojing', 
                'name': '逆天魔晶', 
                'source_type': 'monster',
                'source_level': 'high', 
                'drop_rate': 0.3
            },
            {
                'material_id': 'mieshi_long_he', 
                'name': '灭世龙核', 
                'source_type': 'monster',
                'source_level': 'high', 
                'drop_rate': 0.8
            }
            # ...其他材料...
        ]
        
        # 初始化任务
        quests = [
            # ------------------- 主线任务 -------------------
            {
                'quest_id': 'main_1', 
                'name': '初入修真界', 
                'type': '主线', 
                'level': '下等',
                'required_realm': '炼体境', 
                'required_faction': '',
                'objectives': '{"kill_monster": {"裂海玄龟": 5, "腐骨血蛭": 5}, "collect_material": {"青纹铁": 10, "蚀骨铁屑": 10}}',
                'rewards': '{"gold": 200, "exp": 500, "item": {"裂海玄龟核": 2, "腐骨核": 2}}',
                'reward_type': 'item', 
                'is_repeatable': False
            },
            {
                'quest_id': 'main_2', 
                'name': '妖丹初成', 
                'type': '主线', 
                'level': '下等',
                'required_realm': '蚀骨境', 
                'required_faction': '',
                'objectives': '{"craft_pill": 1, "kill_monster": {"碧眼灵猴": 3, "噬魂夜枭": 3}}',
                'rewards': '{"gold": 300, "exp": 800, "recipe": "pill_base"}',
                'reward_type': 'alchemy', 
                'is_repeatable': False
            },
            
            # ------------------- 支线任务 -------------------
            {
                'quest_id': 'side_1', 
                'name': '采集灵草', 
                'type': '支线', 
                'level': '下等',
                'required_realm': '炼体境', 
                'required_faction': '',
                'objectives': '{"collect_herb": 10}',
                'rewards': '{"gold": 100, "exp": 300, "item": {"灵草": 5}}',
                'reward_type': 'item', 
                'is_repeatable': True
            },
            {
                'quest_id': 'side_2', 
                'name': '讨伐低阶妖兽', 
                'type': '支线', 
                'level': '下等',
                'required_realm': '蚀骨境', 
                'required_faction': '',
                'objectives': '{"kill_monster": {"裂海玄龟": 3, "腐骨血蛭": 3}}',
                'rewards': '{"gold": 150, "exp": 400, "item": {"青纹铁": 5, "蚀骨铁屑": 5}}',
                'reward_type': 'item', 
                'is_repeatable': True
            },
            
            # ------------------- 日常任务 -------------------
            {
                'quest_id': 'daily_1', 
                'name': '基础修炼', 
                'type': '日常', 
                'level': '下等',
                'required_realm': '炼体境', 
                'required_faction': '',
                'objectives': '{"cultivate": 1}',
                'rewards': '{"gold": 50, "exp": 200, "cultivation": 100}',
                'reward_type': 'item', 
                'is_repeatable': True
            },
            {
                'quest_id': 'daily_2', 
                'name': '坊市交易', 
                'type': '日常', 
                'level': '下等',
                'required_realm': '蚀骨境', 
                'required_faction': '',
                'objectives': '{"trade_item": 1}',
                'rewards': '{"gold": 80, "exp": 250, "item": {"低级灵石": 1}}',
                'reward_type': 'item', 
                'is_repeatable': True
            },
            # ------------------- 主线任务 -------------------
            {
                'quest_id': 'main_3', 
                'name': '宗门试炼', 
                'type': '主线', 
                'level': '中等',
                'required_realm': '筑基境', 
                'required_faction': '仙域',
                'objectives': '{"kill_monster": {"乙木灵藤": 5, "熔浆魔蛛": 5}, "craft_weapon": 1}',
                'rewards': '{"gold": 500, "exp": 1500, "item": {"乙木灵藤核": 3, "熔魔核": 3, "recipe": "forge_sword_2"}}',
                'reward_type': 'forging', 
                'is_repeatable': False
            },
            {
                'quest_id': 'main_4', 
                'name': '魔台初成', 
                'type': '主线', 
                'level': '中等',
                'required_realm': '铸魔台', 
                'required_faction': '魔渊',
                'objectives': '{"kill_monster": {"熔浆魔蛛": 5, "乙木灵藤": 5}, "craft_armor": 1}',
                'rewards': '{"gold": 600, "exp": 1800, "item": {"熔魔核": 3, "乙木灵藤核": 3, "recipe": "demon_armor_2"}}',
                'reward_type': 'forging', 
                'is_repeatable': False
            },
            
            # ------------------- 支线任务 -------------------
            {
                'quest_id': 'side_3', 
                'name': '灵植培育', 
                'type': '支线', 
                'level': '中等',
                'required_realm': '筑基境', 
                'required_faction': '',
                'objectives': '{"plant_grow": 1, "collect_material": {"灵草": 15}}',
                'rewards': '{"gold": 250, "exp": 700, "item": {"灵植种子": 2}}',
                'reward_type': 'item', 
                'is_repeatable': True
            },
            {
                'quest_id': 'side_4', 
                'name': '讨伐中级妖兽', 
                'type': '支线', 
                'level': '中等',
                'required_realm': '铸魔台', 
                'required_faction': '',
                'objectives': '{"kill_monster": {"碧眼灵猴": 5, "噬魂夜枭": 5}}',
                'rewards': '{"gold": 300, "exp": 800, "item": {"赤精铁": 8, "聚煞赤晶": 8}}',
                'reward_type': 'item', 
                'is_repeatable': True
            },
            
            # ------------------- 日常任务 -------------------
            {
                'quest_id': 'daily_3', 
                'name': '宗门签到', 
                'type': '日常', 
                'level': '中等',
                'required_realm': '筑基境', 
                'required_faction': '',
                'objectives': '{"sign_in": 1}',
                'rewards': '{"gold": 120, "exp": 400, "faction_rep": 50}',
                'reward_type': 'item', 
                'is_repeatable': True
            },
            {
                'quest_id': 'daily_4', 
                'name': '符箓制作', 
                'type': '日常', 
                'level': '中等',
                'required_realm': '铸魔台', 
                'required_faction': '',
                'objectives': '{"craft_talisman": 1}',
                'rewards': '{"gold": 150, "exp": 450, "item": {"黄符": 2}}',
                'reward_type': 'talisman', 
                'is_repeatable': True
            },
            {
                'quest_id': 'main_5', 
                'name': '元婴化形', 
                'type': '主线', 
                'level': '上等',
                'required_realm': '元婴境', 
                'required_faction': '仙域',
                'objectives': '{"kill_monster": {"庚金铁翼": 5, "冥河骨龙": 5}, "craft_pendant": 1}',
                'rewards': '{"gold": 1000, "exp": 3000, "item": {"庚金铁翼核": 3, "骨龙核": 3, "recipe": "ring_3"}}',
                'reward_type': 'forging', 
                'is_repeatable': False
            },
            {
                'quest_id': 'main_6', 
                'name': '魔胎成型', 
                'type': '主线', 
                'level': '上等',
                'required_realm': '化魔胎', 
                'required_faction': '魔渊',
                'objectives': '{"kill_monster": {"冥河骨龙": 5, "庚金铁翼": 5}, "craft_treasure": 1}',
                'rewards': '{"gold": 1200, "exp": 3500, "item": {"骨龙核": 3, "庚金铁翼核": 3, "recipe": "demon_treasure_2"}}',
                'reward_type': 'forging', 
                'is_repeatable': False
            },
            
            # ------------------- 支线任务 -------------------
            {
                'quest_id': 'side_5', 
                'name': '秘境探索', 
                'type': '支线', 
                'level': '上等',
                'required_realm': '元婴境', 
                'required_faction': '',
                'objectives': '{"explore_secret": 1, "kill_boss": 1}',
                'rewards': '{"gold": 500, "exp": 1500, "item": {"随机灵宝材料": 1}}',
                'reward_type': 'item', 
                'is_repeatable': True
            },
            {
                'quest_id': 'side_6', 
                'name': '讨伐高阶妖兽', 
                'type': '支线', 
                'level': '上等',
                'required_realm': '化魔胎', 
                'required_faction': '',
                'objectives': '{"kill_monster": {"雷狱麒麟": 3, "万蛊母虫": 3}}',
                'rewards': '{"gold": 600, "exp": 1800, "item": {"雷狱麒麟核": 2, "万蛊核": 2}}',
                'reward_type': 'item', 
                'is_repeatable': True
            },
            
            # ------------------- 日常任务 -------------------
            {
                'quest_id': 'daily_5', 
                'name': '跨服论道', 
                'type': '日常', 
                'level': '上等',
                'required_realm': '元婴境', 
                'required_faction': '',
                'objectives': '{"pvp_battle": 1}',
                'rewards': '{"gold": 300, "exp": 800, "honor": 100}',
                'reward_type': 'item', 
                'is_repeatable': True
            },
            {
                'quest_id': 'daily_6', 
                'name': '法宝温养', 
                'type': '日常', 
                'level': '上等',
                'required_realm': '化魔胎', 
                'required_faction': '',
                'objectives': '{"nourish_treasure": 1}',
                'rewards': '{"gold": 350, "exp": 900, "item": {"法宝经验": 500}}',
                'reward_type': 'item', 
                'is_repeatable': True
            }
        ]
        
        # 插入数据...
        # ...插入代码...
        
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor
        
    def fetch_one(self, query: str, params: tuple = ()) -> Dict[str, Any]:
        cursor = self.execute(query, params)
        result = cursor.fetchone()
        return result if result else None
        
    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        cursor = self.execute(query, params)
        return cursor.fetchall()
        
    def close(self):
        self.conn.close()