import sqlalchemy
from critiquebrainz import db
from critiquebrainz.db import exceptions as db_exceptions


def update(entity_id, entity_type):
	"""Updates the average rating of the entity
	
	It does so by collecting all the review_ids for a given entity from review
	and selecting respective revisions with latest timestamp
	and calculating sum and count of ratings 
	
	Args:
		entity_id (uuid): ID of the entity
		entity_type (str): Type of the entity
	"""
	with db.engine.connect() as connection:
		result = connection.execute(sqlalchemy.text("""
			WITH LatestRevisions AS (
				SELECT review_id,
					   MAX("timestamp") created_at
				  FROM revision
				 WHERE review_id in ( 
				 	       SELECT id 
				 	         FROM review
				 	        WHERE entity_id = :entity_id
				 	          AND entity_type = :entity_type)
			  GROUP BY review_id)
			
			SELECT SUM(rating),
			       COUNT(rating)
			  FROM revision
		INNER JOIN LatestRevisions
		        ON revision.review_id = LatestRevisions.review_id
		       AND revision.timestamp = LatestRevisions.created_at
		"""),{
			"entity_id": entity_id,
			"entity_type": entity_type,
		})

		row = result.fetchone()
		if row is None:
			delete(entity_id, entity_type)
			return
	
	#Calulate average rating and update it	
	sum, count = row[0], row[1]
	avg_rating = int(sum / count + 0.5)
	with db.engine.connect() as connection:
		connection.execute(sqlalchemy.text("""
	   		INSERT INTO avg_rating(entity_id, entity_type, rating, count)
				 VALUES (:entity_id, :entity_type, :rating, :count)
	        ON CONFLICT 
	      ON CONSTRAINT avg_rating_pkey
	          DO UPDATE
	                SET rating = EXCLUDED.rating, 
	                	count = EXCLUDED.count
	    """),{
			"entity_id": entity_id,
			"entity_type": entity_type,
			"rating": avg_rating,
			"count": count,
	    })


def delete(entity_id, entity_type):
	"""Deletes the avg_rating, given entity_id and entity_type

	Args: 
		entity_id (uuid): ID of the entity
		entity_type (str): Type of the entity
	"""
	with db.engine.connect() as connection:
		connection.execute(sqlalchemy.text("""
			DELETE 
			  FROM avg_rating
			 WHERE entity_id = :entity_id
			   AND entity_type = :entity_type
		"""), {
			"entity_id": entity_id,
			"entity_type": entity_type,
		})


def get(entity_id, entity_type):
	"""Get average rating from entity_id

	Args: 
		entity_id (uuid): ID of the entity
		entity_type (str): Type of the entity
	Returns:
		Dictionary with the following structure
		{
			"entity_id": uuid,
			"entity_type": str("release group", "event", "place"),
			"rating": int,
			"count": int,
		}
	"""
	with db.engine.connet() as connection:
		result = connection.execute(sqlalchemy.text("""
			SELECT *
			  FROM avg_rating
			 WHERE entity_id = :entity_id
			   AND entity_type = :entity_type
		"""), {
			"entity_id": entity_id,
			"entity_type": entity_type
		})

		avg_rating = result.fetchone()
		if not avg_rating:
			raise db_exceptions.NoDataFoundException("No rating for the entity with ID: {id}".format(id=entity_id))

	return dict(avg_rating)