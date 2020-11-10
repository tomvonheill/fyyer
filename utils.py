def clean_venue_data(form_data):
    clean_form_data = {}
    form_data['seeking_talent'] = [True] if 'True' in form_data['seeking_talent'] else [False]
    for key, value in form_data.items():
        clean_form_data[key] = value[0]
    return clean_form_data