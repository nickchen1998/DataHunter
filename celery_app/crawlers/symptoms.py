import random
import re
import time
from datetime import datetime
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from fake_useragent import UserAgent
from RAGPilot.celery import app
from crawlers.models import Symptom
from langchain_openai import OpenAIEmbeddings


START_POINTS = [
  {
    "department": "內科",
    "start_url": "https://sp1.hso.mohw.gov.tw/doctor/Often_question/type_detail.php?UrlClass=%A4%BA%AC%EC&q_like=0&q_type=%EBC%B3%C2%AFl%A9%CA%A6%E5%BA%DE%AA%A2",
  },
  {
    "department": "外科",
    "start_url": "https://sp1.hso.mohw.gov.tw/doctor/Often_question/type_detail.php?UrlClass=%A5%7E%AC%EC&q_like=0&q_type=%E6%B3%A6%D7",
  },
  {
    "department": "牙科",
    "start_url": "https://sp1.hso.mohw.gov.tw/doctor/Often_question/type_detail.php?UrlClass=%A4%FA%AC%EC&q_like=0&q_type=%F9%AF%B0%A9%B0%A9%A7%E9",
  },
  {
    "department": "骨科",
    "start_url": "https://sp1.hso.mohw.gov.tw/doctor/Often_question/type_detail.php?UrlClass=%B0%A9%AC%EC&q_like=0&q_type=%F9%AF%B0%A9%B0%A9%A7%E9%B3N%AB%E1",
  },
  {
    "department": "眼科",
    "start_url": "https://sp1.hso.mohw.gov.tw/doctor/Often_question/type_detail.php?UrlClass=%B2%B4%AC%EC&q_like=0&q_type=%C5%E7%A5%FA%B0%DD%C3D",
  },
  {
    "department": "肝膽腸胃科",
    "start_url": "https://sp1.hso.mohw.gov.tw/doctor/Often_question/type_detail.php?UrlClass=%A8x%C1x%B8z%ADG%AC%EC&q_like=0&q_type=%E4%FA%A4%DF",
  },
  {
    "department": "耳鼻喉科",
    "start_url": "https://sp1.hso.mohw.gov.tw/doctor/Often_question/type_detail.php?UrlClass=%A6%D5%BB%F3%B3%EF%AC%EC&q_like=0&q_type=%F9%AE%C3E%B5o%AA%A2",
  },
  {
    "department": "皮膚科",
    "start_url": "https://sp1.hso.mohw.gov.tw/doctor/Often_question/type_detail.php?UrlClass=%A5%D6%BD%A7%AC%EC&q_like=0&q_type=%F9%AF%B0%A9%A5%C0%B4%B3",
  }
]


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
    for start_point in START_POINTS:
        if demo:
            symptom_crawler_task(
                department=start_point["department"],
                start_url=start_point["start_url"],
                demo=demo,
            )
            break
        else:
            symptom_crawler_task.delay(
                department=start_point["department"],
                start_url=start_point["start_url"],
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
