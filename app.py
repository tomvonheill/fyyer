#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from config import *
from flask_migrate import Migrate
from utils import clean_venue_data
import sys
from sqlalchemy import func
import datetime
from models import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  try:
    data = {'|'.join([city_state.city, city_state.state]):[] for city_state in db.session.query(Venue.city, Venue.state).distinct()}
    #get the subquery count of show dates after right now
    sq = db.session.query(Show.venue_id, func.count(Show.start_time).label('count')).filter(Show.start_time>datetime.datetime.now()).group_by(Show.venue_id).subquery()

    #outer join with venue
    joined_q = db.session.query(Venue.id, Venue.name, Venue.city, Venue.state, sq.c.count).outerjoin(sq)

    #initial data dict
    for row in joined_q:
      venue_data = {
        "id": row.id,
        "name": row.name,
        "num_upcoming_shows": row.count or 0
      }
      data['|'.join([row.city,row.state])].append(venue_data)

    #expand data dict to normal format
    data = [{'city': key.split('|')[0], 'state': key.split('|')[1], 'venues': value} for key,value in data.items()]

  except:
    print(sys.exc_info())
    pass

  finally:
    db.session.close()

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  serach_term = request.form.get('search_term', '')
  venues = db.session.query(Venue.id, Venue.name).filter(func.lower(Venue.name).contains(func.lower(serach_term)))
  response = {'count':0,
  'data': []}

  for venue in venues:
    sub_data = {
      'id':venue.id,
      'name':venue.name
    }
    response['count'] = response['count']+1
    response['data'].append(sub_data)

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  past_shows = db.session.query(Artist.id,Artist.name, Artist.image_link, Show.start_time).join(Show).join(Venue).filter(
                Show.venue_id == venue_id,
                Show.artist_id == Artist.id,
                Show.start_time < datetime.datetime.now()
      )
  past_shows = [{
    "artist_id": row.id,
    "artist_name": row.name,
    "artist_image_link": row.image_link,
    "start_time": str(row.start_time)
  } for row in past_shows]

  upcoming_shows = db.session.query(Artist.id,Artist.name, Artist.image_link, Show.start_time).join(Show).join(Venue).filter(
              Show.venue_id == venue_id,
              Show.artist_id == Artist.id,
              Show.start_time >= datetime.datetime.now()
    )
  upcoming_shows = [{
    "artist_id": row.id,
    "artist_name": row.name,
    "artist_image_link": row.image_link,
    "start_time": str(row.start_time)
  } for row in upcoming_shows]

  venue = db.session.query(Venue).get(venue_id)

  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  form.validate_on_submit()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = VenueForm()
  if not form.validate_on_submit():
    flash('An error occured. Venue ' + (' ,').join(list(form.errors.keys()))+ ' fields are invalid')
    return render_template('pages/home.html')
  try:
    results = form.data
    genre_data = results['genres']
    del results['genres']
    del results['csrf_token']
    new_venue = Venue(**results)
    db.session.add(new_venue)
    db.session.commit()

    genre_entries = [GenreTagsForVenues(venue_id = new_venue.id, genre = genre) for genre in genre_data]
    db.session.bulk_save_objects(genre_entries)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  
  except:
    db.session.rollback()
    flash('An error occured. Venue ' + request.form['name'] + ' could not be listed. Try again.')
    print(sys.exc_info())
  
  finally:
    db.session.close()

  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  try:
    db.session.delete(db.session.query(Venue).get(venue_id))
    db.session.commit()
    flash('Venue was successfully deleted!')
  
  except:
    db.session.rollback()
    flash('An error occured. Venue  could not be listed. Try again.')
    print(sys.exc_info())
  finally:
    db.session.close()
  return redirect(url_for(venues))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = [{'id': artist.id,
          'name': artist.name}
          for artist in db.session.query(Artist)]
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  serach_term = request.form.get('search_term', '')
  artists = db.session.query(Artist.id, Artist.name).filter(func.lower(Artist.name).contains(func.lower(serach_term)))
  response = {'count':0,
  'data': []}

  for artist in artists:
    sub_data = {
      'id':artist.id,
      'name':artist.name
    }
    response['count'] = response['count']+1
    response['data'].append(sub_data)
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  
  past_shows = db.session.query(Venue.id,Venue.name, Venue.image_link, Show.start_time).join(Show).join(Artist).filter(
              Show.artist_id == artist_id,
              Show.venue_id == Venue.id,
              Show.start_time < datetime.datetime.now()
              )
  past_shows = [{
    "venue_id": row.id,
    "venue_name": row.name,
    "venue_image_link": row.image_link,
    "start_time": str(row.start_time)
    } for row in past_shows]

  upcoming_shows = db.session.query(Venue.id,Venue.name, Venue.image_link, Show.start_time).join(Show).join(Artist).filter(
                Show.artist_id == artist_id,
                Show.venue_id == Venue.id,
              Show.start_time >= datetime.datetime.now()
              )
  upcoming_shows = [{
    "venue_id": row.id,
    "venue_name": row.name,
    "venue_image_link": row.image_link,
    "start_time": str(row.start_time)
    } for row in upcoming_shows]

  artist = db.session.query(Artist).get(artist_id)
  
  data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

  # TODO: populate form with fields from artist with ID <artist_id>
  artist = db.session.query(Artist).get(artist_id)
  form = ArtistForm(obj=artist)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm()
  if not form.validate_on_submit():
    flash('An error occured. Artist ' + (' ,').join(list(form.errors.keys()))+ ' fields are invalid')
    return redirect(url_for(edit_artist))
  try:
    results = form.data
    genre_data = results['genres']
    del results['genres']
    del results['csrf_token']
    db.session.query(Artist).filter(Artist.id == artist_id).update(results)
    
    db.session.query(GenreTagsForArtists).filter(GenreTagsForArtists.artist_id == artist_id).delete()
    genre_entries = [GenreTagsForArtists(artist_id = artist_id, genre = genre) for genre in genre_data]
    db.session.bulk_save_objects(genre_entries)

    db.session.commit()

    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  
  except:
    db.session.rollback()
    flash('An error occured. Artist ' + request.form['name'] + ' could not be updated. Try again.')
    print(sys.exc_info())
  
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = db.session.query(Venue).get(venue_id) 
  form = VenueForm(obj = venue)
  #form = VenueForm(obj=venue)
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm()
  if not form.validate_on_submit():
    flash('An error occured. Venue ' + (' ,').join(list(form.errors.keys()))+ ' fields are invalid')
    return render_template('pages/home.html')
  try:
    results = form.data
    genre_data = results['genres']
    del results['genres']
    del results['csrf_token']
    db.session.query(Venue).filter(Venue.id == venue_id).update(results)
    
    db.session.query(GenreTagsForVenues).filter(GenreTagsForVenues.venue_id == venue_id).delete()
    genre_entries = [GenreTagsForVenues(venue_id = venue_id, genre = genre) for genre in genre_data]
    db.session.bulk_save_objects(genre_entries)

    db.session.commit()

    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  
  except:
    db.session.rollback()
    flash('An error occured. Venue ' + request.form['name'] + ' could not be updated. Try again.')
    print(sys.exc_info())
  
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  form = ArtistForm()
  if not form.validate_on_submit():
    flash('An error occured. Venue ' + (' ,').join(list(form.errors.keys()))+ ' fields are invalid')
    return redirect('/')
  try:
    delete_artist_incase_of_rollback = False
    results = form.data
    genre_data = results['genres']
    del results['genres']
    del results['csrf_token']
    new_artist = Artist(**results)
    db.session.add(new_artist)
    db.session.commit()
    delete_artist_incase_of_rollback = True


    genre_entries = [GenreTagsForArtists(artist_id = new_artist.id, genre = genre) for genre in genre_data]
    db.session.bulk_save_objects(genre_entries)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  
  except:
    db.session.rollback()
    if delete_artist_incase_of_rollback:
      db.session.delete(new_artist)
      db.session.commit()
    flash('An error occured. Artist ' + request.form['name'] + ' could not be listed. Try again.')
    print(sys.exc_info())
  finally:
    db.session.close()

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  query = db.session.query(Show, Venue.name.label('venue_name'), Artist.name.label('artist_name'), Artist.image_link).join(Venue).join(Artist)
  data = [{
    "venue_id": row.Show.venue_id,
    "venue_name": row.venue_name,
    "artist_id": row.Show.artist_id,
    "artist_name": row.artist_name,
    "artist_image_link": row.image_link,
    "start_time": str(row.Show.start_time)
    }
    for row in query]
 
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  form = ShowForm()
  if not form.validate_on_submit():
    flash('An error occured. show ' + (' ,').join(list(form.errors.keys()))+ ' fields are invalid')
    return redirect(url_for(create_shows))
  try:
    results = form.data
    del results['csrf_token']
    new_show = Show(**results)
    db.session.add(new_show)
    db.session.commit()
    flash('Show was successfully listed!')
  
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
