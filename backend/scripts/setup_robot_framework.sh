#!/bin/bash
# Robot Framework + SikuliLibrary 安装脚本 (Linux/macOS)
# 用于配置Robot Framework和SikuliLibrary测试环境

echo "====================================="
echo "Robot Framework + SikuliLibrary 安装"
echo "====================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 检查Python是否安装
echo -e "${YELLOW}1. 检查Python环境...${NC}"
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version)
    echo -e "  ${GREEN}✓ Python已安装: $python_version${NC}"
else
    echo -e "  ${RED}✗ Python未安装${NC}"
    echo -e "  ${RED}请先安装Python 3.8或更高版本${NC}"
    exit 1
fi

# 检查Java是否安装（SikuliX需要）
echo ""
echo -e "${YELLOW}2. 检查Java环境...${NC}"
skip_sikuli=false
if command -v java &> /dev/null; then
    java_version=$(java -version 2>&1 | head -n 1)
    echo -e "  ${GREEN}✓ Java已安装: $java_version${NC}"
else
    echo -e "  ${RED}✗ Java未安装或不在PATH中${NC}"
    echo -e "  ${YELLOW}SikuliLibrary需要Java运行环境${NC}"
    echo -e "  ${YELLOW}请安装Java JDK 8或更高版本${NC}"
    read -p "  是否继续安装（不包含SikuliLibrary）？ (y/N): " continue_without_java
    if [ "$continue_without_java" != "y" ]; then
        exit 1
    fi
    skip_sikuli=true
fi

# 激活虚拟环境
echo ""
echo -e "${YELLOW}3. 激活虚拟环境...${NC}"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "  ${GREEN}✓ 虚拟环境已激活${NC}"
else
    echo -e "  ${YELLOW}⚠ 未找到虚拟环境，将使用全局Python环境${NC}"
fi

# 安装Robot Framework
echo ""
echo -e "${YELLOW}4. 安装Robot Framework...${NC}"
pip3 install --upgrade robotframework
if [ $? -eq 0 ]; then
    robot_version=$(robot --version 2>&1)
    echo -e "  ${GREEN}✓ Robot Framework安装成功${NC}"
else
    echo -e "  ${RED}✗ Robot Framework安装失败${NC}"
    exit 1
fi

# 安装SikuliLibrary
if [ "$skip_sikuli" = false ]; then
    echo ""
    echo -e "${YELLOW}5. 下载并配置SikuliX...${NC}"
    
    sikulix_dir="tools/sikulix"
    sikulix_jar="$sikulix_dir/sikulixide.jar"
    
    mkdir -p "$sikulix_dir"
    
    if [ ! -f "$sikulix_jar" ]; then
        echo -e "  ${YELLOW}下载SikuliX JAR文件...${NC}"
        sikulix_url="https://launchpad.net/sikuli/sikulix/2.0.5/+download/sikulixide-2.0.5.jar"
        if command -v wget &> /dev/null; then
            wget -O "$sikulix_jar" "$sikulix_url"
        elif command -v curl &> /dev/null; then
            curl -L -o "$sikulix_jar" "$sikulix_url"
        else
            echo -e "  ${YELLOW}⚠ 请手动下载SikuliX${NC}"
            echo -e "  ${YELLOW}下载地址: https://raiman.github.io/SikuliX1/downloads.html${NC}"
            echo -e "  ${YELLOW}下载后放置到: $sikulix_jar${NC}"
        fi
        
        if [ -f "$sikulix_jar" ]; then
            echo -e "  ${GREEN}✓ SikuliX下载成功${NC}"
        fi
    else
        echo -e "  ${GREEN}✓ SikuliX已存在${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}6. 安装robotframework-SikuliLibrary...${NC}"
    pip3 install --upgrade robotframework-sikulilibrary
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓ SikuliLibrary安装成功${NC}"
    else
        echo -e "  ${RED}✗ SikuliLibrary安装失败${NC}"
        echo -e "  ${YELLOW}可能需要手动配置Jython环境${NC}"
    fi
fi

# 安装其他依赖
echo ""
echo -e "${YELLOW}7. 安装其他依赖...${NC}"
pip3 install --upgrade Pillow

# 创建资源目录
echo ""
echo -e "${YELLOW}8. 创建测试资源目录...${NC}"
resource_dirs=(
    "artifacts/robot_framework"
    "artifacts/robot_framework/screenshots"
    "examples/robot_resources"
)

for dir in "${resource_dirs[@]}"; do
    mkdir -p "$dir"
    echo -e "  ${GREEN}✓ 创建目录: $dir${NC}"
done

# 验证安装
echo ""
echo -e "${YELLOW}9. 验证安装...${NC}"

all_good=true

# 检查Robot Framework
if command -v robot &> /dev/null; then
    echo -e "  ${GREEN}✓ Robot Framework: 已安装${NC}"
else
    echo -e "  ${RED}✗ Robot Framework: 未安装${NC}"
    all_good=false
fi

# 检查SikuliLibrary
if [ "$skip_sikuli" = false ]; then
    if python3 -c "import SikuliLibrary" 2>/dev/null; then
        echo -e "  ${GREEN}✓ SikuliLibrary: 已安装${NC}"
    else
        echo -e "  ${RED}✗ SikuliLibrary: 未正确安装${NC}"
        all_good=false
    fi
fi

# 检查Pillow
if python3 -c "import PIL" 2>/dev/null; then
    echo -e "  ${GREEN}✓ Pillow: 已安装${NC}"
else
    echo -e "  ${RED}✗ Pillow: 未安装${NC}"
    all_good=false
fi

# 总结
echo ""
echo "====================================="
if [ "$all_good" = true ]; then
    echo -e "${GREEN}✓ 安装完成！${NC}"
    echo ""
    echo -e "${YELLOW}下一步:${NC}"
    echo "1. 准备测试图像资源到 examples/robot_resources/ 目录"
    echo "2. 参考 examples/robot_framework_examples.json 创建测试用例"
    echo "3. 运行测试: robot your_test.robot"
else
    echo -e "${YELLOW}⚠ 安装过程中遇到一些问题${NC}"
    echo "请检查上面的错误信息并手动解决"
fi
echo "====================================="
echo ""

# 创建快速测试脚本
echo -e "${YELLOW}10. 创建快速测试脚本...${NC}"
cat > examples/robot_quick_test.robot << 'EOF'
*** Settings ***
Library    OperatingSystem

*** Test Cases ***
简单测试
    [Documentation]    验证Robot Framework基本功能
    Log    Hello from Robot Framework!
    Should Be Equal    ${2+2}    4
EOF

echo -e "  ${GREEN}✓ 创建快速测试文件: examples/robot_quick_test.robot${NC}"
echo ""
echo -e "${CYAN}运行快速测试: robot examples/robot_quick_test.robot${NC}"

