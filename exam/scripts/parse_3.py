# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "python-docx",
# ]
# ///

from docx import Document
import re
import json

def parse_questions(file_path):
    doc = Document(file_path)
    paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
    
    questions = {
        '判断题': [],
        '单选题': [],
        '多选题': []
    }
    
    current_type = None
    current_question = None
    
    for i, para in enumerate(paragraphs):
        # 检测题型
        if '判断题' in para and '一、' in para:
            # 先保存当前题目（如果有）
            if current_question:
                questions[current_type].append(current_question)
                current_question = None
            current_type = '判断题'
            print(f"切换到题型: {current_type} at line {i}")
            continue
        elif '单选题' in para:
            # 先保存当前题目（如果有）
            if current_question:
                questions[current_type].append(current_question)
                current_question = None
            current_type = '单选题'
            print(f"切换到题型: {current_type} at line {i}")
            continue
        elif '多选题' in para:
            # 先保存当前题目（如果有）
            if current_question:
                questions[current_type].append(current_question)
                current_question = None
            current_type = '多选题'
            print(f"切换到题型: {current_type} at line {i}")
            continue
        
        # 检测题目编号
        # 判断题: （    ）1. 或 (    ) 1.
        if re.match(r'^[（(]\s*[）)]\s*\d+\.', para):
            if current_question:
                questions[current_type].append(current_question)
            # 使用当前题型长度+1作为新ID
            new_id = len(questions[current_type]) + 1
            # 判断题不需要 options 字段
            current_question = {
                'id': new_id,
                'question': para,
                'answer': None
            }
        # 单选题/多选题: 1. 或 (1) 或 1、
        elif re.match(r'^\d+\.', para) or re.match(r'^[（(]\d+[）)]\s*', para):
            # 检查是否是选项行（支持A-E）
            if not re.match(r'^[（(]\s*[A-E]\s*[）)]', para) and not re.match(r'^[A-E][、.]', para):
                if current_question:
                    questions[current_type].append(current_question)
                # 使用当前题型长度+1作为新ID
                new_id = len(questions[current_type]) + 1
                current_question = {
                    'id': new_id,
                    'question': para,
                    'options': [],
                    'answer': None
                }
        # 检测选项 (A) 或 A、（支持A-E）
        elif re.match(r'^[（(]\s*[A-E]\s*[）)]', para) or re.match(r'^[A-E][、.]', para):
            if current_question:
                current_question['options'].append(para)
    
    # 添加最后一个问题
    if current_question:
        questions[current_type].append(current_question)
    
    return questions

def show_sample(questions, qtype, count=2):
    print(f"\n{qtype} 示例 (前{count}题):")
    for i, q in enumerate(questions[qtype][:count]):
        print(f"\n题目 {q['id']}:")
        print(f"  问题: {q['question']}")
        if 'options' in q and q['options']:
            print(f"  选项:")
            for opt in q['options']:
                print(f"    {opt}")
        else:
            print(f"  选项: 无")

# 处理复习题
print(f"{'='*60}")
print("处理理论知识复习题")
print(f"{'='*60}")
questions = parse_questions("../source/第3部分-人工智能训练师_3级_理论知识复习题.docx")

print(f"\n题目统计:")
for qtype, qlist in questions.items():
    print(f"  {qtype}: {len(qlist)} 题")

show_sample(questions, '判断题')
show_sample(questions, '单选题')
show_sample(questions, '多选题')

# 保存
with open('../data/questions_3.json', 'w', encoding='utf-8') as f:
    json.dump(questions, f, ensure_ascii=False, indent=2)

print(f"\n已保存到 ../data/questions_3.json")
