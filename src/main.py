import os
import json
import logging
import argparse
from datetime import date, datetime, timedelta

# 确保 src 目录在 Python 路径中，以便导入其他模块
# 这通常在运行脚本时自动处理，或者可以通过设置 PYTHONPATH
# 或者更好的方式是使用相对导入（如果结构允许）或将项目作为包安装
from scraper import fetch_cv_papers
from filter import filter_papers_by_topic, rate_papers
from html_generator import generate_html_from_json

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 定义项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 定义默认目录
DEFAULT_JSON_DIR = os.path.join(PROJECT_ROOT, 'daily_json')
DEFAULT_HTML_DIR = os.path.join(PROJECT_ROOT, 'daily_html')
DEFAULT_TEMPLATE_DIR = os.path.join(PROJECT_ROOT, 'templates')
DEFAULT_TEMPLATE_NAME = 'paper_template.html' # 确保此模板存在

def main(target_date: date):
    """主执行流程：抓取、过滤、保存、生成HTML。"""
    logging.info(f"开始处理日期: {target_date.isoformat()}")

    # --- 确定 JSON 文件路径 ---
    json_filename = f"{target_date.isoformat()}.json"
    json_filepath = os.path.join(DEFAULT_JSON_DIR, json_filename)
    logging.info(f"目标 JSON 文件路径: {json_filepath}")

    # --- 检查 JSON 文件是否存在 ---
    if os.path.exists(json_filepath):
        logging.info(f"找到已存在的 JSON 文件: {json_filepath}。跳过抓取和过滤步骤。")
        # 不需要加载数据，generate_html_from_json 会直接读取文件
    else:
        logging.info(f"未找到 JSON 文件: {json_filepath}。执行抓取和过滤。")
        # --- 1. 抓取论文 --- #
        logging.info("步骤 1: 抓取 ArXiv cs.CV 论文...")
        # 注意：fetch_cv_papers 内部默认使用 UTC 日期
        raw_papers = fetch_cv_papers(category='cs.CV', specified_date=target_date)
        if not raw_papers:
            logging.warning(f"在 {target_date.isoformat()} 未找到论文或抓取失败。")
            # 如果抓取失败且无 JSON 文件，则无法继续
            return
        logging.info(f"抓取到 {len(raw_papers)} 篇原始论文。")

        # --- 2. 过滤论文、论文打分 --- #
        logging.info("步骤 2: 使用 AI 过滤论文并打分 (主题: image/video/multimodal generation)...")
        # 注意：filter_papers_by_topic 依赖 OPENROUTER_API_KEY 环境变量
        filtered_papers = filter_papers_by_topic(raw_papers, topic="image or video or multimodal generation")
        filtered_papers = rate_papers(filtered_papers)
        # 将filtered_papers按照overall_priority_score降序排序
        filtered_papers.sort(key=lambda x: x.get('overall_priority_score', 0), reverse=True)
        if not filtered_papers:
            logging.warning("没有论文通过过滤。将创建空的 JSON 文件。")
            # 创建一个空列表，以便后续保存为空 JSON
            filtered_papers = []
            # 即使没有过滤后的论文，也可能需要生成一个空的报告，或者在这里停止
            # 这里我们选择继续，生成一个可能为空的报告
        logging.info(f"过滤后剩余 {len(filtered_papers)} 篇论文。")

        # --- 3. 保存为 JSON --- #
        logging.info("步骤 3: 将过滤后的论文保存为 JSON 文件...")

        # --- 3.1 转换日期为字符串 --- #
        logging.info("步骤 3.1: 转换日期时间对象为 ISO 格式字符串以便 JSON 序列化...")
        for paper in filtered_papers:
            if isinstance(paper.get('published_date'), datetime):
                paper['published_date'] = paper['published_date'].isoformat()
            if isinstance(paper.get('updated_date'), datetime):
                paper['updated_date'] = paper['updated_date'].isoformat()

        os.makedirs(DEFAULT_JSON_DIR, exist_ok=True) # 确保目录存在
        try:
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(filtered_papers, f, indent=4, ensure_ascii=False)
            logging.info(f"过滤后的论文已保存到: {json_filepath}")
        except IOError as e:
            logging.error(f"保存 JSON 文件失败: {e}")
            return # 保存失败则无法继续
        except Exception as e:
            logging.error(f"保存 JSON 时发生意外错误: {e}", exc_info=True)
            return

    # --- 4. 生成 HTML (无论 JSON 是新建还是已存在) --- #
    logging.info("步骤 4: 从 JSON 文件生成 HTML 报告...")
    # 再次检查 JSON 文件是否实际存在（以防万一）
    if not os.path.exists(json_filepath):
         logging.error(f"无法找到 JSON 文件 '{json_filepath}' 来生成 HTML。")
         return

    try:
        generate_html_from_json(
            json_file_path=json_filepath,
            template_dir=DEFAULT_TEMPLATE_DIR,
            template_name=DEFAULT_TEMPLATE_NAME,
            output_dir=DEFAULT_HTML_DIR
        )
        logging.info(f"HTML 报告已生成在: {DEFAULT_HTML_DIR}")

        # --- 5. 更新 reports.json --- #
        logging.info("步骤 5: 更新根目录下的 reports.json 文件...")
        reports_json_path = os.path.join(PROJECT_ROOT, 'reports.json')
        try:
            if os.path.exists(DEFAULT_HTML_DIR) and os.path.isdir(DEFAULT_HTML_DIR):
                html_files = [f for f in os.listdir(DEFAULT_HTML_DIR) if f.endswith('.html')]
                # 按文件名（日期）降序排序
                html_files.sort(reverse=True)
                with open(reports_json_path, 'w', encoding='utf-8') as f:
                    json.dump(html_files, f, indent=4, ensure_ascii=False)
                logging.info(f"reports.json 已更新，包含 {len(html_files)} 个报告。")
            else:
                logging.warning(f"HTML 目录 '{DEFAULT_HTML_DIR}' 不存在，无法生成 reports.json。")
                # 如果目录不存在，可以选择创建一个空的 reports.json
                with open(reports_json_path, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=4, ensure_ascii=False)
                logging.info("已创建空的 reports.json。")
        except Exception as e:
            logging.error(f"更新 reports.json 时发生错误: {e}", exc_info=True)

    except FileNotFoundError:
        logging.error(f"模板文件 '{DEFAULT_TEMPLATE_NAME}' 未在 '{DEFAULT_TEMPLATE_DIR}' 中找到。")
    except Exception as e:
        logging.error(f"生成 HTML 时发生意外错误: {e}", exc_info=True)

    logging.info(f"日期 {target_date.isoformat()} 的处理流程完成。")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='抓取、过滤并生成 arXiv cs.CV 论文的每日报告。')
    parser.add_argument(
        '--date',
        type=str,
        help='指定抓取的日期 (YYYY-MM-DD)。如果未指定，默认为 3 天前的 UTC 日期。'
    )

    args = parser.parse_args()

    run_date = None
    if args.date:
        try:
            run_date = datetime.strptime(args.date, '%Y-%m-%d').date()
            logging.info(f"使用用户指定的日期: {run_date.isoformat()}")
        except ValueError:
            logging.error("日期格式无效，请使用 YYYY-MM-DD 格式。退出程序。")
            exit(1)
    else:
        # 如果未指定日期，使用 scraper 中的默认逻辑（通常是几天前）
        # 为了保持一致性，我们在这里计算默认日期，并传递给 main 函数
        # 注意：这里计算的是本地时间的3天前，而 scraper 内部处理时会考虑 UTC
        # 如果需要严格的 UTC 3天前，需要像 scraper 那样使用 timezone.utc
        run_date = date.today() - timedelta(days=3)
        logging.info(f"未指定日期，使用默认日期: {run_date.isoformat()} (本地时间的3天前)")
        # 或者，让 main 函数内部的 fetch_cv_papers 自行处理 None 值，以获取其默认 UTC 日期
        # run_date = None # 取消注释这行以使用 fetch_cv_papers 的默认日期逻辑

    # 确保模板目录和文件存在，否则 HTML 生成会失败
    if not os.path.exists(DEFAULT_TEMPLATE_DIR) or not os.path.exists(os.path.join(DEFAULT_TEMPLATE_DIR, DEFAULT_TEMPLATE_NAME)):
        logging.warning(f"模板目录 '{DEFAULT_TEMPLATE_DIR}' 或模板文件 '{DEFAULT_TEMPLATE_NAME}' 不存在。HTML 生成可能会失败。")
        # 可以考虑在这里创建默认模板或退出

    main(target_date=run_date)