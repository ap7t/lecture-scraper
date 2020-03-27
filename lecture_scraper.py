from selenium import webdriver
import getpass, re, requests
from queue import Queue
from pathlib import Path

class LectureScraper():
    def __init__(self):
        student_num, password = self.get_user_details()
        cwd = Path.cwd()
        self.save_location =  cwd / 'Lectures'
        self.save_location.mkdir(exist_ok=True)
        prefs = {'download.default_directory': str(self.save_location)}
        options = webdriver.ChromeOptions()
        options.add_experimental_option('prefs', prefs)
        try:
            self.driver = webdriver.Chrome(str(cwd / 'chromedriver'), options=options)
        except:
            try:
                self.driver = webdriver.Chrome(str(cwd / 'chromedriver.exe'), options=options)
            except:
                print('Please save the chromedriver executable in this directory')
                quit()
                
        self.driver.get('https://ucc.instructure.com/')
        self.login(student_num, password)
        print('\nLogging in to Canvas\n')
        self.current_mods = ['CS2506', 'CS2511', 'CS2514', 'CS2209', 'CS2505']
        self.recent_downloads = Queue()

    def get_user_details(self):
        ''' Get credentials from user '''

        student_num = input('Enter your student number: ')
        password = getpass.getpass('Password to sign into Canvas: ')
        return student_num, password

    def login(self, student_num, password):
        ''' Login to canvas '''

        ucc_email_in = self.driver.find_element_by_id('username')
        ucc_pass_in = self.driver.find_element_by_id('password')
        ucc_email_in.send_keys(student_num)
        ucc_pass_in.send_keys(password)
        ucc_login_btn = self.driver.find_element_by_xpath('/html/body/div/div/div/div[1]/form/div[4]/button')
        ucc_login_btn.click()
        try:
            incorrect_inp = self.driver.find_element_by_xpath('/html/body/div/div/div/div[1]/section/p')
            self.driver.get('https://ucc.instructure.com/')
            print('\nUsername or password incorrect')
            ucc_email_in = self.driver.find_element_by_id('username')
            ucc_email_in.clear()
            student_num, password = self.get_user_details()
            self.login(student_num, password)
        except:
            pass
        
    def _download(self, link):
        self.driver.get(link)
        download_lec = self.driver.find_element_by_xpath('//*[@id="content"]/div[1]/span/a')
        download_lec.click()
        new_name = download_lec.text[9:] # get rid of the 'Download ' in link on canvas
        self.recent_downloads.put(new_name)
        
    def download_lectures(self, mod_code, mod_url):
        ''' Download all lectures for a module '''
        self.driver.get(mod_url)

        if mod_code == 'CS2511':
            lects = b.driver.find_element_by_xpath('//*[@id="context_module_content_67629"]')
            links = lects.find_elements_by_tag_name('a')
            lec_links = [links[i].get_attribute('href') for i in range(1, len(links), 2)] # some blank links so just use every second one
            for link in lec_links:
                self._download(link)


        elif mod_code == 'CS2505':
            all_links = self.driver.find_elements_by_tag_name('a')  
            lec_links = [link.get_attribute('href') for link in all_links if re.search(r'(The Basics|Layer|^Network Management)', link.text)]
            for link in lec_links:
                self._download(link)
        else:
            all_links = self.driver.find_elements_by_tag_name('a')
            lec_links = [link.get_attribute('href') for link in all_links if re.search(r'(L|Lecture) ?\d{1,2}.*(.(ppt|pdf))$', link.text)]
            for link in lec_links:
                self._download(link)


    def ken(self):
        ''' Get CS2516 lectures '''

        self.driver.get('http://www.cs.ucc.ie/~kb11/teaching/CS2516/Lectures/')
        directory = self.save_location / 'CS2516'
        directory.mkdir()
        content = self.driver.find_element_by_id('maincontent')
        lec_links = [link.get_attribute('href') for link in content.find_elements_by_tag_name('a')]
        print('Downloading CS2516 lectures')
        for link in lec_links:
            filename = link.split('/')[-1]
            if '.pdf' in filename:
                r = requests.get(link, auth=('cs1', 'cs1'))
                with open(str(directory /  filename), 'wb') as f:
                    for chunk in r.iter_content(10000):
                        f.write(chunk)
            

    def get_modules(self):
        ''' Return a dictionary of module codes and urls to module page on canvas '''

        mod_dict = {}
        dash = b.driver.find_element_by_xpath('//*[@id="DashboardCard_Container"]')
        mods = dash.find_elements_by_tag_name('a')
        for mod in mods:
            if re.search(r'^2020-CS\d{4}:', mod.text):
                mod_code = mod.text.split(':')[0][-6:]
                if mod_code in self.current_mods:
                    mod_dict.update({mod_code:mod.get_attribute('href')})

        return mod_dict

    def move_file(self, directory, file):
        ''' Save files into respective module directory'''

        path = self.save_location / file
        new_path = self.save_location / directory  / file
        donwnloaded = moved = False

        while not donwnloaded and not moved:
            try:
                path.rename(new_path)
                downloaded = True
                if new_path.stat().st_size == 0:
                    moved = False
                else:
                    moved = True
                
            except:
                pass
                 

    def scrape(self):
        ''' Scrape lectures '''

        mods = self.get_modules()
        for mod_code, url in mods.items():
            mod_dir = self.save_location / mod_code 
            print(f'Downloading {mod_code} lectures')
            mod_dir.mkdir(exist_ok=True)
            self.download_lectures(mod_code, url)
            while not self.recent_downloads.empty():
                file_to_move = self.recent_downloads.get()
                self.move_file(mod_code, file_to_move)
            print(f'{mod_code} lectures saved\n')
                
        self.ken()    

        print(f'\nLectures be saved at {str(self.save_location)}')
        self.driver.quit()


if __name__ == "__main__":
    b = LectureScraper()
    b.scrape()
