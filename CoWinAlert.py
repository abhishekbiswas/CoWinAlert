from __future__ import print_function, unicode_literals
from PyInquirer import style_from_dict, Token, prompt
from polling import TimeoutException, poll
import datetime
import requests
import json
import os

poll_duration = 7 # No. of seconds poll duration
poll_timeout = 3600 * 5 # 5 hour poll timeout

app_style = style_from_dict({
    Token.Separator: '#cc5454',
    Token.QuestionMark: '#673ab7 bold',
    Token.Selected: '#cc5454',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Instruction: '',  # default
    Token.Answer: '#f44336 bold',
    Token.Question: ''
})

request_headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
    'X-user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36 FKUA/website/41/website/Desktop',
    'Origin': 'https://cdn-api.co-vin.in',
    'Host': 'cdn-api.co-vin.in',
    'Pragma': 'no-cache'
}


def get_states():
    response = requests.get("https://cdn-api.co-vin.in/api/v2/admin/location/states", headers=request_headers)
    state_data = json.loads(response.text)
    states = dict()
    for state_data_instance in state_data["states"]:
        states[state_data_instance["state_name"]] = state_data_instance["state_id"]
    return states


def get_districts(state_id):
    request_url = "https://cdn-api.co-vin.in/api/v2/admin/location/districts/" + str(state_id)
    response = requests.get(request_url, headers=request_headers)
    district_data = json.loads(response.text)
    districts = dict()
    for district_data_instance in district_data["districts"]:
        districts[district_data_instance["district_name"]] = district_data_instance["district_id"]
    return districts


def get_vaccine_slot_strategy1(chosen_district_name, chosen_district_id):
    request_url = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByDistrict?" + "district_id=" \
                  + str(chosen_district_id) + "&" + "date=" \
                  + str((datetime.datetime.today() + datetime.timedelta(days=1)).date().strftime("%d-%m-%Y"))
    response = requests.get(request_url, headers=request_headers)
    slot_data = json.loads(response.text)
    pin_codes = []
    for slot_data_instance in slot_data["sessions"]:
        pin_codes.append(slot_data_instance['pincode'])
    slot_info = dict()
    if len(pin_codes) != 0:
        slot_info[chosen_district_name] = pin_codes
    return slot_info


def get_vaccine_slot_strategy2(chosen_district_name, chosen_district_id):
    request_url = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/calendarByDistrict?" + "district_id=" \
                  + str(chosen_district_id) + "&" + "date=" \
                  + str((datetime.datetime.today() + datetime.timedelta(days=1)).date().strftime("%d-%m-%Y"))
    response = requests.get(request_url, headers=request_headers)
    slot_data = json.loads(response.text)
    pin_codes = []
    for center in slot_data["centers"]:
        for session in center["sessions"]:
            if session['available_capacity'] > 0 and session['min_age_limit'] == 45:
                pin_codes.append(center['pincode'])
    slot_info = dict()
    if len(pin_codes) != 0:
        slot_info[chosen_district_name] = pin_codes
    return slot_info


def print_vaccine_slot_for_chosen_districts(chosen_districts):
    for key in chosen_districts:
        available_slot = get_vaccine_slot_strategy2(key, chosen_districts[key])
        if len(available_slot) != 0:
            print(available_slot)
            os.system('say "Vaccine found!"')


def extract_item_names(items):
    item_names = []
    for key in items:
        item_names.append(key)
    return item_names


def get_district_choice_list(districts):
    district_choice_list = []
    for district in districts:
        district_name_dictionary = dict()
        district_name_dictionary['name'] = district
        district_choice_list.append(district_name_dictionary)
    return district_choice_list


def collect_user_state(states):
    question = [
        {
            'type': 'list',
            'message': 'Select your state ',
            'name': 'State',
            'choices': extract_item_names(states)
        }
    ]
    answer = prompt(question, style=app_style)
    return answer


def collect_user_districts(districts):
    question = [
        {
            'type': 'checkbox',
            'message': 'Select your district(s) ',
            'name': 'Districts',
            'choices': get_district_choice_list(extract_item_names(districts))
        }
    ]
    answers = prompt(question, style=app_style)
    return answers


def main():
    states = get_states()
    state_answer = collect_user_state(states)
    state_id = states[state_answer['State']]
    districts = get_districts(state_id)
    district_answers = collect_user_districts(districts)
    chosen_district_names = district_answers['Districts']
    chosen_districts = dict()
    for chosen_district_name in chosen_district_names:
        chosen_districts[chosen_district_name] = districts[chosen_district_name]
    print_vaccine_slot_for_chosen_districts(chosen_districts)
    poll(lambda: print_vaccine_slot_for_chosen_districts(chosen_districts), timeout=poll_timeout, step=poll_duration)


if __name__ == "__main__":
    main()
