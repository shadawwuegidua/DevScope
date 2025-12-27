"""
DevScope Phase 1 - 数据预置和冷启动功能测试
"""

import os
import sys
import json

# 设置 UTF-8 输出
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from seed_data import (
    initialize_seed_database,
    load_seed_data,
    get_developer_from_fame_hall,
    is_developer_in_fame_hall,
)
from modeling import (
    calculate_confidence_weight,
    is_cold_start,
    prepare_cold_start_data,
    fetch_or_generate_developer_analysis,
    DataPreprocessor,
)

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


def test_seed_data_initialization():
    """测试数据预置初始化"""
    print("\n" + "=" * 70)
    print("[测试 1/4] 数据预置初始化")
    print("=" * 70)
    
    try:
        initialize_seed_database()
        print("✅ 初始化成功")
        return True
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False


def test_load_seed_data():
    """测试加载预置数据"""
    print("\n" + "=" * 70)
    print("[测试 2/4] 加载预置数据")
    print("=" * 70)
    
    try:
        data = load_seed_data()
        assert "metadata" in data, "缺少 metadata"
        assert "developers" in data, "缺少 developers"
        
        dev_count = len(data["developers"])
        print(f"✅ 加载成功")
        print(f"   预置开发者数: {dev_count}")
        
        # 验证名人堂查询
        print("\n   名人堂开发者查询:")
        for username in list(data["developers"].keys())[:3]:
            profile = data["developers"][username]["profile"]
            print(f"   - {username:15s} | {profile['name']}")
        
        return True
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return False


def test_cold_start_logic():
    """测试冷启动逻辑"""
    print("\n" + "=" * 70)
    print("[测试 3/4] 冷启动逻辑")
    print("=" * 70)
    
    try:
        # 测试置信度权重
        print("\n置信度权重计算:")
        test_cases = [0, 2, 5, 10, 15, 20]
        for count in test_cases:
            weight = calculate_confidence_weight(count, threshold=10)
            status = "冷启动" if is_cold_start(count, threshold=5) else "正常"
            print(f"   项目数: {count:2d} | 权重: {weight:.3f} | 状态: {status}")
        
        # 测试冷启动数据准备
        print("\n冷启动数据准备:")
        cold_data = prepare_cold_start_data(
            username="newbie",
            project_count=2,
            primary_language="Python"
        )
        print(f"   用户: newbie (项目数: 2)")
        print(f"   是否冷启动: {cold_data['is_cold_start']}")
        print(f"   置信度权重: {cold_data['confidence_weight']}")
        print(f"   推断开发者类型: {cold_data['developer_type']}")
        print(f"   社区平均技术倾向: {list(cold_data['community_tendency'].keys())}")
        
        print("✅ 冷启动逻辑测试通过")
        return True
    except Exception as e:
        print(f"❌ 冷启动逻辑测试失败: {e}")
        return False


def test_data_preprocessor():
    """测试数据预处理器"""
    print("\n" + "=" * 70)
    print("[测试 4/4] 数据预处理器集成")
    print("=" * 70)
    
    try:
        processor = DataPreprocessor(cold_start_threshold=5)
        
        # 测试场景 1: 冷启动
        print("\n场景 1: 新手开发者（冷启动）")
        result1 = processor.process(
            username="newbie",
            project_count=2,
            user_tendency={"Python": 0.6, "JavaScript": 0.4},
            primary_language="Python"
        )
        print(f"   用户: {result1['username']}")
        print(f"   冷启动标记: {result1['is_cold_start']}")
        print(f"   置信度权重: {result1['confidence_weight']:.1%}")
        print(f"   融合后的技术倾向:")
        for tech, prob in sorted(
            result1['tendency'].items(), key=lambda x: x[1], reverse=True
        )[:5]:
            print(f"     - {tech:15s}: {prob:.3f}")
        print(f"   解释: {result1['explanation']}")
        
        # 测试场景 2: 正常情况
        print("\n场景 2: 经验丰富开发者（正常）")
        result2 = processor.process(
            username="veteran",
            project_count=20,
            user_tendency={
                "Python": 0.35,
                "JavaScript": 0.25,
                "Go": 0.20,
                "Rust": 0.15,
                "Java": 0.05,
            },
            primary_language="Python"
        )
        print(f"   用户: {result2['username']}")
        print(f"   冷启动标记: {result2['is_cold_start']}")
        print(f"   置信度权重: {result2['confidence_weight']:.1%}")
        print(f"   技术倾向保持不变: {result2['is_cold_start'] == False}")
        print(f"   解释: {result2['explanation']}")
        
        # 测试场景 3: 获取名人堂开发者
        print("\n场景 3: 名人堂开发者")
        fame_result = fetch_or_generate_developer_analysis("torvalds")
        print(f"   来源: {fame_result['source']}")
        if fame_result['source'] == 'fame_hall':
            print(f"   ✅ 成功从名人堂获取数据")
            profile = fame_result['data']['profile']
            print(f"   开发者: {profile['name']}")
            print(f"   类型: {profile['developer_type']}")
        
        print("\n✅ 数据预处理器测试通过")
        return True
    except Exception as e:
        print(f"❌ 数据预处理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "=" * 70)
    print("DevScope Phase 1 - 数据预置与冷启动功能测试")
    print("=" * 70)
    
    results = []
    
    # 运行所有测试
    results.append(("种子数据初始化", test_seed_data_initialization()))
    results.append(("加载预置数据", test_load_seed_data()))
    results.append(("冷启动逻辑", test_cold_start_logic()))
    results.append(("数据预处理器", test_data_preprocessor()))
    
    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} | {test_name}")
    
    print(f"\n总体: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 Phase 1 数据预置模块完全就绪！")
        return 0
    else:
        print("\n⚠️  部分测试未通过，请检查错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())
