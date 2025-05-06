import random
import re
import time
import json
import pathlib
from datetime import datetime
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
from DataHunter.celery import app

from symptoms.models import Symptom
from langchain_openai import OpenAIEmbeddings


def get_paragraph(browser: Chrome, symptom: str, department: str):
    for paragraph in browser.find_elements(By.CSS_SELECTOR, "ul.QAunit"):
        try:
            subject = paragraph.find_element(By.CSS_SELECTOR, "li.subject").text

            asker_info = paragraph.find_element(By.CSS_SELECTOR, "li.asker").text
            match = re.search(r'／([男女])／.*?,(\d{4}/\d{2}/\d{2})', asker_info)
            gender = match.group(1)
            question_time = datetime.strptime(match.group(2), '%Y/%m/%d')

            question = paragraph.find_element(By.CSS_SELECTOR, "li.ask").text

            answer = paragraph.find_element(By.CSS_SELECTOR, "li.ans").text
            answer_time = datetime.strptime(match.group(2), '%Y/%m/%d')

            data = dict(
                subject_id=int(subject.split(" ")[0].replace("#", "")),
                subject="".join(subject.split(" ")[1:]),
                symptom=symptom,
                question=question,
                gender=gender,
                question_time=question_time,
                answer=answer,
                department=department,
                answer_time=answer_time,
            )
            yield data
        except Exception as e:
            print(e)
            continue


@app.task()
def period_send_symptom_crawler_task():
    dataset_path = pathlib.Path(__file__).parent / "datasets.json"
    with open(dataset_path, "r", encoding="utf-8") as f:
        for dataset in json.load(f):
            symptom_crawler_task(
                department=dataset["department"],
                start_url=dataset["start_url"],
            )


@app.task()
def symptom_crawler_task(department: str, start_url: str):
    options = Options()
    options.add_argument("--headless")
    options.add_argument(f'user-agent={UserAgent().random}')
    browser = Chrome(options=options)
    browser.maximize_window()

    browser.get(start_url)

    symptom_select_menu = browser.find_element(By.CSS_SELECTOR, "select[name='q_type']")
    symptom_list = [tmp.get_attribute("value") for tmp in symptom_select_menu.find_elements(
        By.TAG_NAME, "option") if tmp.get_attribute("value")]

    for symptom in symptom_list:
        url = (f"https://sp1.hso.mohw.gov.tw/doctor/Often_question/type_detail.php?"
               f"q_type={symptom}&UrlClass={department}")
        browser.get(url)
        datas = []
        page = 1

        while browser.find_elements(By.CSS_SELECTOR, "ul.QAunit"):
            datas.extend(list(get_paragraph(
                browser=browser, department=department, symptom=symptom)))

            page += 1
            tmp_url = url + f"&PageNo={page}"
            time.sleep(random.randint(4, 8))
            browser.get(tmp_url)

        for data in datas:
            if Symptom.objects.filter(subject_id=data["subject_id"]).exists():
                continue

            clean_question = data["question"].replace(" ", "").replace("\n", "")
            Symptom.objects.create(
                subject_id=data["subject_id"],
                department=data["department"],
                symptom=data["symptom"],
                question=data["question"],
                answer=data["answer"],
                gender=data["gender"],
                question_time=data["question_time"],
                answer_time=data["answer_time"],
                question_embeddings=OpenAIEmbeddings(
                    model="text-embedding-3-small",
                ).embed_query(clean_question),
            )

    browser.quit()
