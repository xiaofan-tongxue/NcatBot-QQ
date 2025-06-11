from database import Database
import json

def initialize_database():
    db = Database()
    
    # 添加一些基础丹方
    alchemy_recipes = [
        {
            'recipe_id': 'pill_base',
            'name': '筑基丹',
            'grade': '凡品',
            'sub_grade': '中',
            'required_level': 1,
            'ingredients': {'灵草': 3, '妖兽内丹': 1},
            'effect': '突破炼体境'
        },
        # ...其他丹方...
    ]
    
    # 初始化材料来源
    materials = [
        {'material_id': '妖兽内丹', 'name': '妖兽内丹', 'source_type': 'monster', 'source_level': 'low', 'drop_rate': 0.3},
        # ...其他材料...
    ]
    
    # 初始化任务
    quests = [
        {
            'quest_id': 'quest_low_1',
            'name': '采集灵草',
            'type': '日常',
            'level': '下等',
            'required_realm': '炼体境',
            'objectives': {'collect_herb': 5},
            'rewards': {'gold': 100},
            'reward_type': 'item',
            'is_repeatable': True
        },
        {
            'quest_id': 'quest_med_1',
            'name': '讨伐中级妖兽',
            'type': '支线',
            'level': '中等',
            'required_realm': '金丹境',
            'objectives': {'kill_monster': 3},
            'rewards': {},
            'reward_type': 'alchemy',
            'is_repeatable': False
        },
        # ...其他任务...
    ]
    
    print("数据库初始化完成")
    db.close()

if __name__ == "__main__":
    initialize_database()