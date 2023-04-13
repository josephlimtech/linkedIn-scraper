import asyncio
from playwright.async_api import async_playwright
import random
import pytz
import helpers
import xpaths
import connection
import constants
import loguru


async def scrape_linkedin(proxy=None, *args, **kwargs):
    while True:
        async with async_playwright() as driver:
            country = helpers.get_country()
            print(country)
            browser = await driver.firefox.launch(
                headless=True,
                args=['--start-maximized'],
                firefox_user_prefs=constants.FIREFOX_SETTINGS
            )

            timezone_id = random.choice(pytz.all_timezones)
            context = await browser.new_context(
                timezone_id=timezone_id,
                accept_downloads=True,
                is_mobile=False,
                has_touch=False,
                proxy=proxy
            )

            page = await context.new_page()
            await page.bring_to_front()
            # screen_width, screen_height = pyautogui.size()
            await page.set_viewport_size(
                {
                    "width": 1920,
                    "height": 1080
                }
            )

            await page.add_init_script(
                constants.SPOOF_FINGERPRINT % helpers.generate_device_specs()
            )
            await page.goto(helpers.get_url(location=country))
            total_num = int(
                await page.locator(xpaths.JOB_TOTAL_NUM).text_content()
            )
            total_num = 100 if total_num > 100 else total_num
            for index in range(1, total_num+1):
                await page.locator(f'({xpaths.JOB_LI})[{index}]').click()
                ads_id = await page.locator(
                    f'({xpaths.JOB_LI})[{index}]//div[@data-entity-urn]'
                ).get_attribute('data-entity-urn')
                ads_id = ads_id.split("urn:li:jobPosting:")[1]
                company_name = await helpers.safe_get_element_text(
                    page, xpaths.COMPANY_NAME
                )
                location = await helpers.safe_get_element_text(
                    page, xpaths.LOCATION
                )
                title = await helpers.safe_get_element_text(
                    page, xpaths.TITLE
                )
                level = await helpers.safe_get_element_text(
                    page, xpaths.SENIORITY_LEVEL, timeout=100
                )
                employement_type = await helpers.safe_get_element_text(
                    page, xpaths.EMPLOYEMENT_TYPE, timeout=100
                )
                await asyncio.sleep(random.randint(1, 2))
                await page.locator(xpaths.SHOW_MORE).click()
                info = await helpers.get_element_text(
                    page, xpaths.BODY_INFO, False
                )
                await connection.create_ads(
                    ads_id, location, info.strip(), company_name,
                    title, 1, employement_type, level, country
                )
                loguru.logger.info(f"Finished {ads_id}")
                await asyncio.sleep(random.randint(1, 6))


asyncio.run(scrape_linkedin())
