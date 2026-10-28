"""Semantic checks for Ohio and Pennsylvania location imports and canonical records."""
import re
OHIO_COUNTIES = {'Hancock', 'Wood', 'Meigs', 'Madison', 'Monroe', 'Lake', 'Van Wert', 'Clark', 'Trumbull', 'Ross', 'Medina', 'Erie', 'Montgomery', 'Butler', 'Wayne', 'Preble', 'Allen', 'Licking', 'Delaware', 'Pike', 'Summit', 'Highland', 'Morrow', 'Adams', 'Franklin', 'Coshocton', 'Holmes', 'Perry', 'Portage', 'Hocking', 'Knox', 'Crawford', 'Darke', 'Brown', 'Ashland', 'Hamilton', 'Richland', 'Hardin', 'Miami', 'Morgan', 'Auglaize', 'Noble', 'Belmont', 'Guernsey', 'Marion', 'Seneca', 'Scioto', 'Mercer', 'Carroll', 'Greene', 'Paulding', 'Huron', 'Putnam', 'Union', 'Fulton', 'Fayette', 'Defiance', 'Ashtabula', 'Sandusky', 'Athens', 'Warren', 'Henry', 'Pickaway', 'Lorain', 'Jefferson', 'Williams', 'Harrison', 'Clermont', 'Muskingum', 'Wyandot', 'Columbiana', 'Ottawa', 'Gallia', 'Stark', 'Lucas', 'Logan', 'Mahoning', 'Fairfield', 'Champaign', 'Tuscarawas', 'Vinton', 'Jackson', 'Cuyahoga', 'Clinton', 'Washington', 'Lawrence', 'Shelby', 'Geauga'}
PENNSYLVANIA_COUNTIES = {'Adams', 'Allegheny', 'Armstrong', 'Beaver', 'Bedford', 'Berks', 'Blair', 'Bradford', 'Bucks', 'Butler', 'Cambria', 'Cameron', 'Carbon', 'Centre', 'Chester', 'Clarion', 'Clearfield', 'Clinton', 'Columbia', 'Crawford', 'Cumberland', 'Dauphin', 'Delaware', 'Elk', 'Erie', 'Fayette', 'Forest', 'Franklin', 'Fulton', 'Greene', 'Huntingdon', 'Indiana', 'Jefferson', 'Juniata', 'Lackawanna', 'Lancaster', 'Lawrence', 'Lebanon', 'Lehigh', 'Luzerne', 'Lycoming', 'McKean', 'Mercer', 'Mifflin', 'Monroe', 'Montgomery', 'Montour', 'Northampton', 'Northumberland', 'Perry', 'Philadelphia', 'Pike', 'Potter', 'Schuylkill', 'Snyder', 'Somerset', 'Sullivan', 'Susquehanna', 'Tioga', 'Union', 'Venango', 'Warren', 'Washington', 'Wayne', 'Westmoreland', 'Wyoming', 'York'}
def validate_pennsylvania_location(location):
 # The Department of Health roster has no county; county is present only from an accepted geocode.
 if 'county' in location and location['county'] not in PENNSYLVANIA_COUNTIES:raise ValueError('Invalid Pennsylvania county: '+str(location['county']))
 for key in ('name','city','address'):
  value=location.get(key)
  if not isinstance(value,str) or not value.strip():raise ValueError('Missing location '+key)
 if re.search(r'\b(dispensary|cannabis|LLC)\b',location['city'],re.I):raise ValueError('Business name in city field')
 postal=location.get('postal_code','')
 if not re.fullmatch(r'\d{5}(-\d{4})?',postal) or not 150<=int(postal[:3])<=196:raise ValueError('Invalid Pennsylvania ZIP code')
 if ('latitude' in location)!=('longitude' in location):raise ValueError('Coordinates must be a pair')
 if 'latitude' in location and not (39.7<=location['latitude']<=42.3 and -80.6<=location['longitude']<=-74.6):raise ValueError('Coordinates outside Pennsylvania')
def validate_location_fields(location):
 if location['state']=='PA':return validate_pennsylvania_location(location)
 if location['state']!='OH':return
 if location['county'] not in OHIO_COUNTIES:raise ValueError('Invalid Ohio county: '+str(location['county']))
 for key in ('name','city','address'):
  value=location.get(key)
  if not isinstance(value,str) or not value.strip():raise ValueError('Missing location '+key)
 if re.search(r'\b(dispensary|cannabis|LLC)\b',location['city'],re.I):raise ValueError('Business name in city field')
 if location['city'] in OHIO_COUNTIES and location['name']==location['city']:raise ValueError('City in business name field')
 if not re.fullmatch(r'\d{5}',location['postal_code']) or not 430<=int(location['postal_code'][:3])<=459:raise ValueError('Invalid Ohio ZIP code')
