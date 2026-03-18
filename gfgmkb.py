import sys
import subprocess
import time
import threading
import queue
import os
import logging

# ==========================================
# 1. OS-AGNOSTIC AUTO-INSTALLER
# ==========================================
try:
    import selenium
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
except ImportError:
    print("[!] Selenium not found. Auto-installing dependencies for your OS...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium", "--quiet"])
        print("[+] Dependencies installed successfully! Restarting...\n")
        import os
        os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as e:
        print(f"[-] Failed to install dependencies. Please run: pip install selenium")
        sys.exit(1)

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)

# ==========================================
# 2. VIDEO DESTROYER CLASS
# ==========================================
class GFGVideoAutomator:
    def __init__(self):
        self.course_dashboard_url = "https://www.geeksforgeeks.org/batch/dsa-juet-guna?tab=Resources" 
        self.driver = self._setup_driver()
        self.fast_wait = WebDriverWait(self.driver, 5) 
        self.wait = WebDriverWait(self.driver, 15)      
        self.long_wait = WebDriverWait(self.driver, 60) 
        self.completed_sub_sections = set() 
        self.SELECTORS = {
            'accordion_arrow': (By.CSS_SELECTOR, 'div[class*="batch_arrow_icon"]'),
            'batch_item': (By.CSS_SELECTOR, 'div[class*="batch_item__"]'),
            'item_title': (By.CSS_SELECTOR, 'div[class*="batch_title_publish_container__"]'),
            'item_meta': (By.CSS_SELECTOR, 'div[class*="batch_content_meta__"]'),
            'resume_button': (By.CSS_SELECTOR, 'button[class*="batch_track_progress__btn"]'),
            'tab_menu_container': (By.CSS_SELECTOR, 'div[class*="ui pointing secondary menu"]'),
            'tab_item': (By.CSS_SELECTOR, 'a.item'),
            'video_sidebar_tab': (By.XPATH, "//div[contains(@class, 'sidebar_tabs') and p[contains(text(), 'videos')]]"),
            'sidebar_video_item': (By.CSS_SELECTOR, 'a[class*="sidebar_item"]'),
            'back_to_home_btn': (By.CSS_SELECTOR, 'p[class*="sidebar_backTo_home"]')
        }

    def _setup_driver(self):
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--remote-debugging-port=9222") 
        profile_path = os.path.abspath("./gfg_chrome_profile")
        options.add_argument(f"user-data-dir={profile_path}")
        logging.info("Initializing Selenium for Videos...")
        return webdriver.Chrome(options=options)

    def dismiss_popups(self):
        try:
            close_btns = self.driver.find_elements(By.XPATH, "//button[normalize-space()='Close']")
            for btn in close_btns:
                if btn.is_displayed():
                    logging.info("Intercepted a pop-up! Smashing the Close button...")
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)
        except Exception:
            pass

    def inject_anti_pause_script(self):
        script = """
            try {
                if (!window.visibilitySpoofed) {
                    Object.defineProperty(document, 'visibilityState', {get: function () { return 'visible'; }, configurable: true});
                    Object.defineProperty(document, 'hidden', {get: function () { return false; }, configurable: true});
                    window.visibilitySpoofed = true;
                }
                document.dispatchEvent(new Event('visibilitychange'));
            } catch(e) {}
        """
        self.driver.execute_script(script)

    def force_video_restart(self):
        logging.info("Attempting to force video to start from 0:00...")
        script = """
            let v = document.querySelector('video');
            if(v) {
                v.currentTime = 0;
                v.play();
                return true;
            }
            return false;
        """
        for _ in range(5):
            if self.driver.execute_script(script):
                logging.info("SUCCESS: Video reset to 0:00 and is playing.")
                return
            time.sleep(1)
        logging.warning("Could not find the HTML5 <video> tag.")

    def is_video_completed(self, video_element):
        try:
            images = video_element.find_elements(By.TAG_NAME, 'img')
            for img in images:
                src = img.get_attribute('src')
                if src and 'Group11(1)' in src: return True
        except NoSuchElementException: pass
        try:
            progress = video_element.find_element(By.CSS_SELECTOR, 'div[class*="ui progress"]')
            if progress.get_attribute('data-percent') == '100': return True
        except NoSuchElementException: pass
        return False

    def login_check(self):
        self.driver.get(self.course_dashboard_url)
        try:
            self.long_wait.until(EC.presence_of_element_located(self.SELECTORS['accordion_arrow']))
            logging.info("Course dashboard loaded successfully.")
        except TimeoutException:
            logging.warning("Please log in manually in the browser window within the next 120 seconds.")
            WebDriverWait(self.driver, 120).until(EC.presence_of_element_located(self.SELECTORS['accordion_arrow']))
            logging.info("Manual login detected. Proceeding.")

    def get_valid_tab_menus(self):
        raw_menus = self.driver.find_elements(*self.SELECTORS['tab_menu_container'])
        valid_menus = [m for m in raw_menus if m.is_displayed() and not any(x in m.text.upper() for x in ["RESOURCES", "CONTEST", "LEADERBOARD"])]
        return valid_menus

    def start(self):
        try:
            self.login_check()
            self.master_navigation_loop()
        except Exception as e:
            logging.critical(f"A critical error occurred: {str(e)}")
        finally:
            self.teardown()

    def master_navigation_loop(self):
        self.wait.until(EC.presence_of_all_elements_located(self.SELECTORS['accordion_arrow']))
        time.sleep(2)
        accordions_raw = self.driver.find_elements(*self.SELECTORS['accordion_arrow'])
        total_acc = len(accordions_raw)
        accordions_to_process = min(7, total_acc) 
        logging.info(f"Video Bot Locked. Processing first {accordions_to_process} sections in DESCENDING order.")
        
        for acc_idx in range(accordions_to_process - 1, -1, -1):
            logging.info(f"--- Focusing strictly on Section {acc_idx + 1} of {accordions_to_process} ---")
            self.exhaust_accordion(acc_idx)
        logging.info("STRICT WORKFLOW COMPLETE! Target sections exhausted.")

    def exhaust_accordion(self, acc_idx):
        while True:
            self.dismiss_popups()
            self.wait.until(EC.presence_of_all_elements_located(self.SELECTORS['accordion_arrow']))
            time.sleep(2)
            arrows = self.driver.find_elements(*self.SELECTORS['accordion_arrow'])
            if acc_idx >= len(arrows): return

            arrow = arrows[acc_idx]
            parent_div = arrow.find_element(By.XPATH, "./../..")
            
            try: section_title = parent_div.text.split('\n')[0].strip()
            except: section_title = f"Section {acc_idx + 1}"

            if "batch_open" not in parent_div.get_attribute("class"):
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", arrow)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", arrow) # JS Click override
                time.sleep(1.5)

            menus = self.get_valid_tab_menus()
            if menus:
                tabs = menus[0].find_elements(*self.SELECTORS['tab_item'])
                tab_count = len(tabs)
                accordion_still_has_work = False

                for tab_idx in range(tab_count):
                    fresh_menus = self.get_valid_tab_menus()
                    if not fresh_menus: break
                    fresh_tabs = fresh_menus[0].find_elements(*self.SELECTORS['tab_item'])
                    if tab_idx >= len(fresh_tabs): break

                    tab = fresh_tabs[tab_idx]
                    tab_name = tab.text.strip()
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tab)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", tab) # JS Click override
                    time.sleep(1.5)
                    
                    logging.info(f"Scanning Tab: [{tab_name}] in '{section_title}'")
                    if self.scan_and_process_rows(parent_div):
                        accordion_still_has_work = True
                        break 
                
                if not accordion_still_has_work:
                    logging.info(f"All tabs in '{section_title}' are fully exhausted!")
                    return 
            else:
                logging.info(f"Scanning rows in '{section_title}'")
                if self.scan_and_process_rows(parent_div): pass 
                else:
                    logging.info(f"All rows in '{section_title}' are fully exhausted!")
                    return 

    def scan_and_process_rows(self, container_div):
        self.dismiss_popups()
        rows = container_div.find_elements(*self.SELECTORS['batch_item'])
        visible_rows = [r for r in rows if r.is_displayed()]
        for row in visible_rows:
            try:
                title_elem = row.find_element(*self.SELECTORS['item_title'])
                row_title = title_elem.text.strip().split('\n')[0]
            except Exception: continue

            if row_title in self.completed_sub_sections: continue

            try:
                meta_elem = row.find_element(*self.SELECTORS['item_meta'])
                if "Video" not in meta_elem.text:
                    logging.info(f"Skipping '{row_title}' -> No videos detected.")
                    self.completed_sub_sections.add(row_title)
                    continue
            except NoSuchElementException: continue 

            try:
                btn = row.find_element(*self.SELECTORS['resume_button'])
                logging.info(f"Target Sub-Section Found: '{row_title}'. Entering player...")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", btn) # JS Click override
                time.sleep(3) 
                
                self.watch_videos_in_player(row_title)
                self.escape_to_dashboard()
                self.completed_sub_sections.add(row_title)
                return True 
            except Exception as e:
                logging.error(f"Failed to interact with row '{row_title}': {str(e)}")
                continue
        return False

    def watch_videos_in_player(self, row_title):
        try:
            video_tab = self.fast_wait.until(EC.element_to_be_clickable(self.SELECTORS['video_sidebar_tab']))
            self.driver.execute_script("arguments[0].click();", video_tab)
            time.sleep(2) 
        except TimeoutException:
            logging.warning(f"No 'Videos' sidebar tab found in '{row_title}'. Completing early.")
            return

        self.inject_anti_pause_script()
        first_video_played = False

        while True:
            try: self.wait.until(EC.presence_of_all_elements_located(self.SELECTORS['sidebar_video_item']))
            except TimeoutException: break
                
            sidebar_videos = self.driver.find_elements(*self.SELECTORS['sidebar_video_item'])
            next_uncompleted_video = None
            target_index = -1
            
            for index, video_element in enumerate(sidebar_videos):
                if not self.is_video_completed(video_element):
                    next_uncompleted_video = video_element
                    target_index = index
                    break
            
            if not next_uncompleted_video:
                logging.info(f"All videos in '{row_title}' are 100% complete!")
                break 

            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_uncompleted_video)
            time.sleep(1) 
            self.driver.execute_script("arguments[0].click();", next_uncompleted_video)
            time.sleep(3)
            
            if not first_video_played:
                logging.info("Executing User Hack: Clicking away and back to force autoplay...")
                try:
                    if target_index + 1 < len(sidebar_videos):
                        temp_video = sidebar_videos[target_index + 1]
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", temp_video)
                        self.driver.execute_script("arguments[0].click();", temp_video)
                        time.sleep(3) 
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_uncompleted_video)
                        self.driver.execute_script("arguments[0].click();", next_uncompleted_video)
                        time.sleep(3)
                except Exception: pass
                first_video_played = True

            self.force_video_restart()
            logging.info("Video playback in progress. Entering 15-second monitoring loop...")
            
            while True:
                time.sleep(15) 
                self.inject_anti_pause_script() 
                try:
                    clean_current_video = self.driver.find_elements(*self.SELECTORS['sidebar_video_item'])[target_index]
                    if self.is_video_completed(clean_current_video):
                        logging.info("Ding! Video marked as complete by GFG. Moving to next.")
                        break
                except Exception: pass

    def escape_to_dashboard(self):
        logging.info("Clicking GFG Back Button...")
        try:
            back_btn = self.wait.until(EC.element_to_be_clickable(self.SELECTORS['back_to_home_btn']))
            self.driver.execute_script("arguments[0].click();", back_btn)
            self.wait.until(EC.presence_of_element_located(self.SELECTORS['accordion_arrow']))
            time.sleep(2)
        except Exception as e:
            logging.error(f"Back button failed ({str(e)}). Forcing URL reload.")
            self.driver.get(self.course_dashboard_url)
            time.sleep(3)

    def teardown(self):
        logging.info("Automation session complete. Closing browser.")
        self.driver.quit()


# ==========================================
# 3. ARTICLE DESTROYER CLASS
# ==========================================
class GFGArticleAutomator:
    def __init__(self):
        self.course_dashboard_url = "https://www.geeksforgeeks.org/batch/dsa-juet-guna?tab=Resources" 
        self.driver = self._setup_driver()
        self.fast_wait = WebDriverWait(self.driver, 5) 
        self.wait = WebDriverWait(self.driver, 15)      
        self.long_wait = WebDriverWait(self.driver, 60) 
        self.completed_sub_sections = set() 
        self.SELECTORS = {
            'accordion_arrow': (By.CSS_SELECTOR, 'div[class*="batch_arrow_icon"]'),
            'batch_item': (By.CSS_SELECTOR, 'div[class*="batch_item__"]'),
            'item_title': (By.CSS_SELECTOR, 'div[class*="batch_title_publish_container__"]'),
            'item_meta': (By.CSS_SELECTOR, 'div[class*="batch_content_meta__"]'),
            'resume_button': (By.CSS_SELECTOR, 'button[class*="batch_track_progress__btn"]'),
            'tab_menu_container': (By.CSS_SELECTOR, 'div[class*="ui pointing secondary menu"]'),
            'tab_item': (By.CSS_SELECTOR, 'a.item'),
            'article_sidebar_tab': (By.XPATH, "//div[contains(@class, 'sidebar_tabs') and p[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'article')]]"),
            'sidebar_item': (By.CSS_SELECTOR, 'a[class*="sidebar_item"]'),
            'mark_as_read_btn': (By.XPATH, "//button[contains(@class, 'GFG_MarkAsRead') or contains(text(), 'Mark as Read')]"),
            'back_to_home_btn': (By.CSS_SELECTOR, 'p[class*="sidebar_backTo_home"]')
        }

    def _setup_driver(self):
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--remote-debugging-port=9222") 
        profile_path = os.path.abspath("./gfg_chrome_profile")
        options.add_argument(f"user-data-dir={profile_path}")
        logging.info("Initializing Selenium for Articles...")
        return webdriver.Chrome(options=options)

    def dismiss_popups(self):
        try:
            close_btns = self.driver.find_elements(By.XPATH, "//button[normalize-space()='Close']")
            for btn in close_btns:
                if btn.is_displayed():
                    logging.info("Intercepted a pop-up! Smashing the Close button...")
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)
        except Exception:
            pass

    def is_item_completed(self, element):
        try:
            images = element.find_elements(By.TAG_NAME, 'img')
            for img in images:
                src = img.get_attribute('src')
                if src and 'Group11(1)' in src: return True
        except NoSuchElementException: pass
        try:
            progress = element.find_element(By.CSS_SELECTOR, 'div[class*="ui progress"]')
            if progress.get_attribute('data-percent') == '100': return True
        except NoSuchElementException: pass
        return False

    def login_check(self):
        self.driver.get(self.course_dashboard_url)
        try:
            self.long_wait.until(EC.presence_of_element_located(self.SELECTORS['accordion_arrow']))
        except TimeoutException:
            logging.warning("Please log in manually within the next 120 seconds.")
            WebDriverWait(self.driver, 120).until(EC.presence_of_element_located(self.SELECTORS['accordion_arrow']))

    def get_valid_tab_menus(self):
        raw_menus = self.driver.find_elements(*self.SELECTORS['tab_menu_container'])
        return [m for m in raw_menus if m.is_displayed() and not any(x in m.text.upper() for x in ["RESOURCES", "CONTEST", "LEADERBOARD"])]

    def start(self):
        try:
            self.login_check()
            self.master_navigation_loop()
        except Exception as e: logging.critical(f"Error: {e}")
        finally: self.teardown()

    def master_navigation_loop(self):
        self.wait.until(EC.presence_of_all_elements_located(self.SELECTORS['accordion_arrow']))
        time.sleep(2)
        total_acc = len(self.driver.find_elements(*self.SELECTORS['accordion_arrow']))
        accordions_to_process = min(7, total_acc) 
        
        logging.info(f"Article Bot Locked. Processing first {accordions_to_process} sections in DESCENDING order.")
        for acc_idx in range(accordions_to_process - 1, -1, -1):
            logging.info(f"--- Focusing on Section {acc_idx + 1} ---")
            self.exhaust_accordion(acc_idx)
        logging.info("ARTICLE WORKFLOW COMPLETE!")

    def exhaust_accordion(self, acc_idx):
        while True:
            self.dismiss_popups()
            self.wait.until(EC.presence_of_all_elements_located(self.SELECTORS['accordion_arrow']))
            time.sleep(2)
            arrows = self.driver.find_elements(*self.SELECTORS['accordion_arrow'])
            if acc_idx >= len(arrows): return

            arrow = arrows[acc_idx]
            parent_div = arrow.find_element(By.XPATH, "./../..")
            
            try: section_title = parent_div.text.split('\n')[0].strip()
            except: section_title = f"Section {acc_idx + 1}"

            if "batch_open" not in parent_div.get_attribute("class"):
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", arrow)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", arrow) # JS Click override
                time.sleep(1.5)

            menus = self.get_valid_tab_menus()
            if menus:
                tabs = menus[0].find_elements(*self.SELECTORS['tab_item'])
                accordion_still_has_work = False
                for tab_idx in range(len(tabs)):
                    fresh_menus = self.get_valid_tab_menus()
                    if not fresh_menus: break
                    fresh_tabs = fresh_menus[0].find_elements(*self.SELECTORS['tab_item'])
                    if tab_idx >= len(fresh_tabs): break

                    tab = fresh_tabs[tab_idx]
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tab)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", tab) # JS Click override
                    time.sleep(1.5)
                    
                    if self.scan_and_process_rows(parent_div):
                        accordion_still_has_work = True
                        break 
                if not accordion_still_has_work: return 
            else:
                if self.scan_and_process_rows(parent_div): pass 
                else: return 

    def scan_and_process_rows(self, container_div):
        self.dismiss_popups()
        rows = container_div.find_elements(*self.SELECTORS['batch_item'])
        for row in [r for r in rows if r.is_displayed()]:
            try: row_title = row.find_element(*self.SELECTORS['item_title']).text.strip().split('\n')[0]
            except Exception: continue

            if row_title in self.completed_sub_sections: continue

            try:
                meta_text = row.find_element(*self.SELECTORS['item_meta']).text
                if "Article" not in meta_text and "Articles" not in meta_text:
                    self.completed_sub_sections.add(row_title)
                    continue
            except NoSuchElementException: continue 

            try:
                btn = row.find_element(*self.SELECTORS['resume_button'])
                logging.info(f"Target Article Section: '{row_title}'. Entering...")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", btn) # JS Click override
                time.sleep(3) 
                
                self.read_articles_in_player(row_title)
                self.escape_to_dashboard()
                self.completed_sub_sections.add(row_title)
                return True 
            except Exception as e:
                logging.error(f"Error: {e}")
                continue
        return False

    def read_articles_in_player(self, row_title):
        try:
            article_tab = self.fast_wait.until(EC.element_to_be_clickable(self.SELECTORS['article_sidebar_tab']))
            self.driver.execute_script("arguments[0].click();", article_tab)
            time.sleep(2) 
        except TimeoutException: return

        last_attempted_index = -1
        stuck_counter = 0

        while True:
            try: self.wait.until(EC.presence_of_all_elements_located(self.SELECTORS['sidebar_item']))
            except TimeoutException: break
                
            sidebar_items = self.driver.find_elements(*self.SELECTORS['sidebar_item'])
            next_uncompleted_article = None
            target_index = -1
            
            for index, item_element in enumerate(sidebar_items):
                if not self.is_item_completed(item_element):
                    next_uncompleted_article = item_element
                    target_index = index
                    break
            
            if not next_uncompleted_article: break 

            if target_index == last_attempted_index:
                stuck_counter += 1
                if stuck_counter >= 2:
                    self.driver.refresh()
                    time.sleep(4)
                    stuck_counter = 0
                    try:
                        tab = self.fast_wait.until(EC.element_to_be_clickable(self.SELECTORS['article_sidebar_tab']))
                        self.driver.execute_script("arguments[0].click();", tab)
                        time.sleep(2)
                    except TimeoutException: pass
                    continue
            else:
                last_attempted_index = target_index
                stuck_counter = 0

            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_uncompleted_article)
            time.sleep(0.5) 
            self.driver.execute_script("arguments[0].click();", next_uncompleted_article)
            time.sleep(1.5) 
            
            try:
                self.driver.execute_script("""
                    let contentBox = document.querySelector('div[class*="batch_content_container"]') || document.documentElement;
                    contentBox.scrollTo(0, contentBox.scrollHeight);
                """)
                time.sleep(1) 
                mark_btn = self.fast_wait.until(EC.presence_of_element_located(self.SELECTORS['mark_as_read_btn']))
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", mark_btn)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", mark_btn)
                logging.info("Clicked 'Mark as Read'.")
                time.sleep(2) 
            except TimeoutException: time.sleep(1)

    def escape_to_dashboard(self):
        try:
            back_btn = self.wait.until(EC.element_to_be_clickable(self.SELECTORS['back_to_home_btn']))
            self.driver.execute_script("arguments[0].click();", back_btn)
            self.wait.until(EC.presence_of_element_located(self.SELECTORS['accordion_arrow']))
            time.sleep(2)
        except Exception:
            self.driver.get(self.course_dashboard_url)
            time.sleep(3)

    def teardown(self):
        self.driver.quit()


# ==========================================
# 4. QUIZ DESTROYER CLASS
# ==========================================
class GFGQuizAutomator:
    def __init__(self):
        self.course_dashboard_url = "https://www.geeksforgeeks.org/batch/dsa-juet-guna?tab=Resources" 
        self.driver = self._setup_driver()
        self.fast_wait = WebDriverWait(self.driver, 5) 
        self.wait = WebDriverWait(self.driver, 15)      
        self.long_wait = WebDriverWait(self.driver, 60) 
        self.completed_sub_sections = set() 
        self.SELECTORS = {
            'accordion_arrow': (By.CSS_SELECTOR, 'div[class*="batch_arrow_icon"]'),
            'batch_item': (By.CSS_SELECTOR, 'div[class*="batch_item__"]'),
            'item_title': (By.CSS_SELECTOR, 'div[class*="batch_title_publish_container__"]'),
            'item_meta': (By.CSS_SELECTOR, 'div[class*="batch_content_meta__"]'),
            'resume_button': (By.CSS_SELECTOR, 'button[class*="batch_track_progress__btn"]'),
            'tab_menu_container': (By.CSS_SELECTOR, 'div[class*="ui pointing secondary menu"]'),
            'tab_item': (By.CSS_SELECTOR, 'a.item'),
            'mcq_sidebar_tab': (By.XPATH, "//div[contains(@class, 'sidebar_tabs') and p[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'mcq') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'quiz')]]"),
            'action_button': (By.XPATH, "//button[normalize-space()='Submit Response' or normalize-space()='Submitted']"),
            'first_option_label': (By.XPATH, "(//div[contains(@class, 'QuizRadioBtn_radio_container')])[1]"),
            'next_btn': (By.XPATH, "//button[contains(., 'Next')]"),
            'back_to_home_btn': (By.CSS_SELECTOR, 'p[class*="sidebar_backTo_home"]')
        }

    def _setup_driver(self):
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--remote-debugging-port=9222") 
        profile_path = os.path.abspath("./gfg_chrome_profile")
        options.add_argument(f"user-data-dir={profile_path}")
        logging.info("Initializing Selenium for Quizzes...")
        return webdriver.Chrome(options=options)

    def dismiss_popups(self):
        try:
            close_btns = self.driver.find_elements(By.XPATH, "//button[normalize-space()='Close']")
            for btn in close_btns:
                if btn.is_displayed():
                    logging.info("Intercepted a pop-up! Smashing the Close button...")
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)
        except Exception:
            pass

    def inject_anti_pause_script(self):
        script = """
            try {
                if (!window.visibilitySpoofed) {
                    Object.defineProperty(document, 'visibilityState', {get: function () { return 'visible'; }, configurable: true});
                    Object.defineProperty(document, 'hidden', {get: function () { return false; }, configurable: true});
                    window.visibilitySpoofed = true;
                }
                document.dispatchEvent(new Event('visibilitychange'));
            } catch(e) {}
        """
        self.driver.execute_script(script)

    def login_check(self):
        self.driver.get(self.course_dashboard_url)
        try:
            self.long_wait.until(EC.presence_of_element_located(self.SELECTORS['accordion_arrow']))
        except TimeoutException:
            logging.warning("Please log in manually within the next 120 seconds.")
            WebDriverWait(self.driver, 120).until(EC.presence_of_element_located(self.SELECTORS['accordion_arrow']))

    def get_valid_tab_menus(self):
        raw_menus = self.driver.find_elements(*self.SELECTORS['tab_menu_container'])
        return [m for m in raw_menus if m.is_displayed() and not any(x in m.text.upper() for x in ["RESOURCES", "CONTEST", "LEADERBOARD"])]

    def start(self):
        try:
            self.login_check()
            self.master_navigation_loop()
        except Exception as e: logging.critical(f"Error: {e}")
        finally: self.teardown()

    def master_navigation_loop(self):
        self.wait.until(EC.presence_of_all_elements_located(self.SELECTORS['accordion_arrow']))
        time.sleep(2)
        total_acc = len(self.driver.find_elements(*self.SELECTORS['accordion_arrow']))
        accordions_to_process = min(7, total_acc) 
        
        logging.info(f"Quiz Bot Locked. Processing {accordions_to_process} sections in DESCENDING order.")
        for acc_idx in range(accordions_to_process - 1, -1, -1):
            logging.info(f"--- Focusing on Section {acc_idx + 1} ---")
            self.exhaust_accordion(acc_idx)
        logging.info("QUIZ WORKFLOW COMPLETE!")

    def exhaust_accordion(self, acc_idx):
        while True:
            self.dismiss_popups()
            self.wait.until(EC.presence_of_all_elements_located(self.SELECTORS['accordion_arrow']))
            time.sleep(2)
            arrows = self.driver.find_elements(*self.SELECTORS['accordion_arrow'])
            if acc_idx >= len(arrows): return

            arrow = arrows[acc_idx]
            parent_div = arrow.find_element(By.XPATH, "./../..")
            
            try: section_title = parent_div.text.split('\n')[0].strip()
            except: section_title = f"Section {acc_idx + 1}"

            if "batch_open" not in parent_div.get_attribute("class"):
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", arrow)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", arrow) # JS Click override
                time.sleep(1.5)

            menus = self.get_valid_tab_menus()
            if menus:
                tabs = menus[0].find_elements(*self.SELECTORS['tab_item'])
                accordion_still_has_work = False
                for tab_idx in range(len(tabs)):
                    fresh_menus = self.get_valid_tab_menus()
                    if not fresh_menus: break
                    fresh_tabs = fresh_menus[0].find_elements(*self.SELECTORS['tab_item'])
                    if tab_idx >= len(fresh_tabs): break

                    tab = fresh_tabs[tab_idx]
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tab)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", tab) # JS Click override
                    time.sleep(1.5)
                    
                    if self.scan_and_process_rows(parent_div):
                        accordion_still_has_work = True
                        break 
                if not accordion_still_has_work: return 
            else:
                if self.scan_and_process_rows(parent_div): pass 
                else: return 

    def scan_and_process_rows(self, container_div):
        self.dismiss_popups()
        rows = container_div.find_elements(*self.SELECTORS['batch_item'])
        for row in [r for r in rows if r.is_displayed()]:
            try: row_title = row.find_element(*self.SELECTORS['item_title']).text.strip().split('\n')[0]
            except Exception: continue

            if row_title in self.completed_sub_sections: continue

            try:
                meta_text = row.find_element(*self.SELECTORS['item_meta']).text.upper()
                if "MCQ" not in meta_text and "QUIZ" not in meta_text:
                    self.completed_sub_sections.add(row_title)
                    continue
            except NoSuchElementException: continue 

            try:
                btn = row.find_element(*self.SELECTORS['resume_button'])
                logging.info(f"Target Quiz Section: '{row_title}'. Entering...")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", btn) # JS Click override
                time.sleep(3) 
                
                self.solve_quiz_in_player(row_title)
                self.escape_to_dashboard()
                self.completed_sub_sections.add(row_title)
                return True 
            except Exception as e:
                logging.error(f"Error: {e}")
                continue
        return False

    def solve_quiz_in_player(self, row_title):
        self.inject_anti_pause_script()
        try:
            quiz_tab = self.fast_wait.until(EC.element_to_be_clickable(self.SELECTORS['mcq_sidebar_tab']))
            self.driver.execute_script("arguments[0].click();", quiz_tab)
            time.sleep(2) 
        except TimeoutException: pass

        question_number = 1
        while True:
            if question_number > 20:
                logging.warning("20 Question Killswitch triggered. Escaping.")
                break

            time.sleep(2) 
            try:
                action_btn = self.fast_wait.until(EC.presence_of_element_located(self.SELECTORS['action_button']))
                btn_text = action_btn.text.strip()
            except TimeoutException: break

            if btn_text == "Submitted":
                logging.info("Question already 'Submitted'. Skipping.")
            else:
                try:
                    first_label = self.driver.find_element(*self.SELECTORS['first_option_label'])
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_label)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", first_label)
                    time.sleep(1) 
                except NoSuchElementException: break

                try:
                    self.driver.execute_script("arguments[0].click();", action_btn)
                    WebDriverWait(self.driver, 5).until(EC.text_to_be_present_in_element(self.SELECTORS['action_button'], "Submitted"))
                except Exception: pass

            try:
                next_btn = self.driver.find_element(*self.SELECTORS['next_btn'])
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", next_btn)
                question_number += 1
            except NoSuchElementException: break

    def escape_to_dashboard(self):
        try:
            back_btn = self.wait.until(EC.element_to_be_clickable(self.SELECTORS['back_to_home_btn']))
            self.driver.execute_script("arguments[0].click();", back_btn)
            self.wait.until(EC.presence_of_element_located(self.SELECTORS['accordion_arrow']))
            time.sleep(2)
        except Exception:
            self.driver.get(self.course_dashboard_url)
            time.sleep(3)

    def teardown(self):
        self.driver.quit()


# ==========================================
# 5. MASTER HUB & LAUNCHER LOGIC
# ==========================================
def print_banner():
    print("==================================================================")
    print("                 GFG COURSE AUTOMATION BOT")
    print("==================================================================")
    print("READ CAREFULLY BEFORE CONTINUING:")
    print("1. LOGIN: A Chrome window will pop up. You MUST log in manually ")
    print("   within 120 seconds on the FIRST run.")
    print("2. DO NOT MINIMIZE: Keep the browser window visible on your screen.")
    print("3. MULTI-DEVICE WARNING: Do NOT log into this account elsewhere.")
    print("4. HANDS OFF: Once it starts clicking, let it work.")
    print("==================================================================\n")

def get_user_choice():
    print("SELECT YOUR STARTING POINT:")
    print("[1] Start with Videos")
    print("[2] Start with Articles")
    print("[3] Start with Quizzes")
    print("\nWaiting 20 seconds for your choice... (Default is [2] Articles)")

    def get_input(q):
        q.put(input("Enter 1, 2, or 3: "))

    q = queue.Queue()
    input_thread = threading.Thread(target=get_input, args=(q,))
    input_thread.daemon = True
    input_thread.start()

    try:
        choice = q.get(timeout=20)
        return choice.strip()
    except queue.Empty:
        print("\n[!] Time is up! Proceeding with Default Order.")
        return "2"

def execute_bot(bot_type):
    print(f"\n>>> FIRING UP: {bot_type} DESTROYER <<<")
    try:
        if bot_type == "Video":
            bot = GFGVideoAutomator()
        elif bot_type == "Article":
            bot = GFGArticleAutomator()
        elif bot_type == "Quiz":
            bot = GFGQuizAutomator()
        bot.start()
        print(f">>> FINISHED: {bot_type} DESTROYER <<<\n")
    except Exception as e:
        print(f"[-] Critical Error running {bot_type} bot: {e}")

def main():
    print_banner()
    choice = get_user_choice()

    if choice == "1":
        print("\n[+] Order locked: Videos -> Articles -> Quizzes")
        order = ["Video", "Article", "Quiz"]
    elif choice == "3":
        print("\n[+] Order locked: Quizzes -> Articles -> Videos")
        order = ["Quiz", "Article", "Video"]
    else:
        print("\n[+] Order locked: Articles -> Quizzes -> Videos")
        order = ["Article", "Quiz", "Video"]

    for bot_type in order:
        execute_bot(bot_type)
        time.sleep(2)

    print("==================================================================")
    print("                 ALL AUTOMATION TASKS COMPLETE!")
    print("==================================================================")

if __name__ == "__main__":
    main()

