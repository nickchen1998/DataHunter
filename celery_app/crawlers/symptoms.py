import random
import re
import time
import json
import pathlib
from datetime import datetime
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
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


            if Symptom.objects.filter(subject_id=subject.split(" ")[0].replace("#", "")).exists():
                continue

            clean_question = question.replace(" ", "").replace("\n", "")
            Symptom.objects.create(
                subject_id=int(subject.split(" ")[0].replace("#", "")),
                subject="".join(subject.split(" ")[1:]),
                symptom=symptom,
                question=question,
                gender=gender,
                question_time=question_time,
                answer=answer,
                department=department,
                answer_time=answer_time,
                question_embeddings=OpenAIEmbeddings(
                    model="text-embedding-3-small",
                ).embed_query(clean_question),
            )
        except Exception as e:
            print(e)
            continue


@app.task()
def period_send_symptom_crawler_task(demo=False):
    dataset_path = pathlib.Path(__file__).parent.parent / "datasets" / "symptoms.json"
    with open(dataset_path, "r", encoding="utf-8") as f:
        for dataset in json.load(f):
            if demo:
                symptom_crawler_task(
                    department=dataset["department"],
                    start_url=dataset["start_url"],
                    demo=demo,
                )
                break
            else:
                symptom_crawler_task.delay(
                    department=dataset["department"],
                    start_url=dataset["start_url"],
                )


@app.task()
def symptom_crawler_task(department: str, start_url: str, demo=False):
    command_executor = 'http://selenium-hub:4444/wd/hub'
    if demo:
        command_executor = 'http://localhost:4444/wd/hub'

    options = Options()
    options.add_argument("--headless")
    options.add_argument(f'user-agent={UserAgent().random}')
    browser = webdriver.Remote(
        command_executor=command_executor,
        options=options
    )
    browser.maximize_window()

    browser.get(start_url)

    symptom_select_menu = browser.find_element(By.CSS_SELECTOR, "select[name='q_type']")
    symptom_list = [tmp.get_attribute("value") for tmp in symptom_select_menu.find_elements(
        By.TAG_NAME, "option") if tmp.get_attribute("value")]

    for symptom in symptom_list:
        url = (f"https://sp1.hso.mohw.gov.tw/doctor/Often_question/type_detail.php?"
               f"q_type={symptom}&UrlClass={department}")
        browser.get(url)
        page = 1

        while browser.find_elements(By.CSS_SELECTOR, "ul.QAunit"):
            get_paragraph(browser=browser, department=department, symptom=symptom)

            page += 1
            tmp_url = url + f"&PageNo={page}"

            time.sleep(random.randint(4, 8))
            browser.get(tmp_url)

    browser.quit()
