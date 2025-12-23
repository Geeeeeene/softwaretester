"""
测试Claude API连接和账户状态
"""
import anthropic
import httpx
import sys
from app.core.config import settings

def test_claude_api():
    """测试Claude API连接"""
    print("=" * 60)
    print("测试Claude API连接")
    print("=" * 60)
    
    # 检查配置
    api_key = settings.CLAUDE_API_KEY
    base_url = settings.CLAUDE_BASE_URL
    model = settings.CLAUDE_MODEL
    
    if not api_key:
        print("❌ 错误: 未配置CLAUDE_API_KEY")
        return False
    
    print(f"✅ API Key: {api_key[:20]}...")
    print(f"✅ Base URL: {base_url}")
    print(f"✅ Model: {model}")
    print()
    
    # 创建HTTP客户端（设置超时）
    http_client = httpx.Client(
        timeout=httpx.Timeout(
            connect=30.0,
            read=60.0,  # 测试用60秒就够了
            write=30.0,
            pool=30.0
        )
    )
    
    # 创建Claude客户端
    try:
        if base_url:
            client = anthropic.Anthropic(
                api_key=api_key,
                base_url=base_url,
                http_client=http_client
            )
            print(f"🔧 使用代理: {base_url}")
        else:
            client = anthropic.Anthropic(
                api_key=api_key,
                http_client=http_client
            )
            print("🔧 使用官方API")
        print()
    except Exception as e:
        print(f"❌ 创建客户端失败: {e}")
        return False
    
    # 测试简单请求
    print("📤 发送测试请求...")
    try:
        message = client.messages.create(
            model=model,
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": "请回复'测试成功'"
                }
            ]
        )
        
        response_text = message.content[0].text
        print(f"✅ API调用成功！")
        print(f"📝 响应: {response_text}")
        print()
        print("=" * 60)
        print("✅ Claude API工作正常，账户状态良好")
        print("=" * 60)
        return True
        
    except anthropic.APIError as e:
        error_msg = str(e)
        print(f"❌ Claude API错误: {error_msg}")
        print()
        
        # 分析错误类型
        if "401" in error_msg or "authentication" in error_msg.lower() or "invalid" in error_msg.lower():
            print("⚠️  可能的原因:")
            print("   1. API密钥无效或已过期")
            print("   2. API密钥格式错误")
            print("   3. 账户被禁用")
        elif "429" in error_msg or "rate limit" in error_msg.lower():
            print("⚠️  可能的原因:")
            print("   1. 请求频率过高（速率限制）")
            print("   2. 配额已用完")
        elif "402" in error_msg or "payment" in error_msg.lower() or "billing" in error_msg.lower():
            print("⚠️  可能的原因:")
            print("   1. 账户欠费")
            print("   2. 付款方式无效")
            print("   3. 需要充值")
        elif "timeout" in error_msg.lower():
            print("⚠️  可能的原因:")
            print("   1. 网络连接问题")
            print("   2. 代理服务器响应慢或不可用")
            print("   3. 代理服务商账户欠费或配额用完")
            print("   4. 请求超时")
            print()
            print("💡 建议检查:")
            print("   1. 访问代理服务商网站检查账户状态")
            print("   2. 检查代理服务商账户余额")
            print("   3. 尝试直接使用官方API（如果API Key支持）")
        else:
            print("⚠️  未知错误，请查看完整错误信息")
        
        print()
        print("=" * 60)
        print("❌ Claude API调用失败")
        print("=" * 60)
        return False
        
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        print()
        print("=" * 60)
        print("❌ 测试失败")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = test_claude_api()
    sys.exit(0 if success else 1)

