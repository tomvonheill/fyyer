from flask import Flask
from flask_moment import Moment
from config import *

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable = False)
    address = db.Column(db.String(120), nullable = False)
    city = db.Column(db.String(120), nullable = False)
    state = db.Column(db.String(120), nullable = False)
    phone = db.Column(db.String(120), nullable = False)
    website = db.Column(db.String(120), nullable = True)
    facebook_link = db.Column(db.String, nullable = True)
    seeking_talent = db.Column(db.Boolean, nullable = False)
    seeking_description = db.Column(db.String, nullable = True)
    image_link = db.Column(db.String(500), nullable = True)

    genres = db.relationship('GenreTagsForVenues', backref='venue')
    shows = db.relationship('Show', backref='venue')
    

# TODO: implement any missing fields, as a database migration using Flask-Migrate

class GenreTagsForVenues(db.Model):
  __tablename__ = 'venue_genre_tags'

  venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), primary_key = True)
  genre = db.Column(db.String(20), primary_key = True)

  def __repr__(self):
    return f'{self.genre}'

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable = False)
    city = db.Column(db.String(120), nullable = False)
    state = db.Column(db.String(120), nullable = False)
    phone = db.Column(db.String(120), nullable = False)
    image_link = db.Column(db.String(500), nullable = True)
    facebook_link = db.Column(db.String(120), nullable = True)
    website = db.Column(db.String, nullable = True)
    seeking_venue = db.Column(db.Boolean, nullable = False)
    seeking_description = db.Column(db.String, nullable = True)

    genres = db.relationship('GenreTagsForArtists', backref='artist', cascade = 'all, delete-orphan')
    shows = db.relationship('Show', backref='artist')


# TODO: implement any missing fields, as a database migration using Flask-Migrate

class GenreTagsForArtists(db.Model):
  __tablename__ = 'artist_genre_tags'

  artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), primary_key = True)
  genre = db.Column(db.String(20), primary_key = True)
  
  def __repr__(self):
    return f'{self.genre}'

class Show(db.Model):
  __tablename__ = 'show'
  
  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))
  venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'))
  start_time = db.Column(db.DateTime, nullable=False)

  def __repr__(self):
    return f'{self.id, self.artist_id, self.venue_id, self.start_time}'