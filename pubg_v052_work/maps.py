"""Nominal PUBG map sizes; strategies are NOT map-validated physics."""
MAPS = {'Erangel':8000,'Miramar':8000,'Taego':8000,'Vikendi':8000,'Deston':8000,'Rondo':8000,'Sanhok':4000,'Paramo':3000,'Karakin':2000,'Haven (legacy)':1000}
# Community references, not official physics. All non-Erangel maps uncalibrated.
PROFILES = {
 'Erangel': {'distance':600,'switch':120,'speed':'200~210','source':'2022 community 600m guide; user-recorded 1125m trajectory'},
 'Miramar': {'distance':600,'switch':120,'speed':'200~210','source':'2022 community 3 big maps guidance; unvalidated for current patch'},
 'Sanhok': {'distance':1100,'switch':120,'speed':'200~210','source':'2022 community Sanhok 1.1km guide; unvalidated'},
 'Taego': {'distance':600,'switch':120,'speed':'200~210','source':'2022 community guide; exploding plane: exit near target; unvalidated'},
}
for _name in MAPS:
 if _name not in PROFILES:
  PROFILES[_name]={'distance':600,'switch':120,'speed':'200~210','source':'generic community baseline only; no verified map-specific formula'}
SOURCES=['https://www.youtube.com/watch?v=HM2XSzs5kMA','https://support.pubg.com/hc/en-us/articles/115004171393-Parachute-System','https://senseos.gg/guides/pubg-battlegrounds/map-sizes/']
