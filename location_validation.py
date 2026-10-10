"""Semantic checks for Ohio location imports and canonical records."""
import re
OHIO_COUNTIES = {'Hancock', 'Wood', 'Meigs', 'Madison', 'Monroe', 'Lake', 'Van Wert', 'Clark', 'Trumbull', 'Ross', 'Medina', 'Erie', 'Montgomery', 'Butler', 'Wayne', 'Preble', 'Allen', 'Licking', 'Delaware', 'Pike', 'Summit', 'Highland', 'Morrow', 'Adams', 'Franklin', 'Coshocton', 'Holmes', 'Perry', 'Portage', 'Hocking', 'Knox', 'Crawford', 'Darke', 'Brown', 'Ashland', 'Hamilton', 'Richland', 'Hardin', 'Miami', 'Morgan', 'Auglaize', 'Noble', 'Belmont', 'Guernsey', 'Marion', 'Seneca', 'Scioto', 'Mercer', 'Carroll', 'Greene', 'Paulding', 'Huron', 'Putnam', 'Union', 'Fulton', 'Fayette', 'Defiance', 'Ashtabula', 'Sandusky', 'Athens', 'Warren', 'Henry', 'Pickaway', 'Lorain', 'Jefferson', 'Williams', 'Harrison', 'Clermont', 'Muskingum', 'Wyandot', 'Columbiana', 'Ottawa', 'Gallia', 'Stark', 'Lucas', 'Logan', 'Mahoning', 'Fairfield', 'Champaign', 'Tuscarawas', 'Vinton', 'Jackson', 'Cuyahoga', 'Clinton', 'Washington', 'Lawrence', 'Shelby', 'Geauga'}
def validate_location_fields(location):
 if location['state']!='OH':return
 if location['county'] not in OHIO_COUNTIES:raise ValueError('Invalid Ohio county: '+str(location['county']))
 for key in ('name','city','address'):
  value=location.get(key)
  if not isinstance(value,str) or not value.strip():raise ValueError('Missing location '+key)
 if re.search(r'\b(dispensary|cannabis|LLC)\b',location['city'],re.I):raise ValueError('Business name in city field')
 if location['city'] in OHIO_COUNTIES and location['name']==location['city']:raise ValueError('City in business name field')
 if not re.fullmatch(r'\d{5}',location['postal_code']) or not 430<=int(location['postal_code'][:3])<=459:raise ValueError('Invalid Ohio ZIP code')
