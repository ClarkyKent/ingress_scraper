# ingress_scraper

original API by https://github.com/lc4t/ingress-api
since it was last modified in 2017, since URL of intel map has changed so installing ingressAPI via pip will install version that have old url. 


**Attention: Remember scrapping too often and big areas can cause account's ban. Don't use your private accounts.**

In order to make API work you need cookies from ingress's intel site. 
1. Log into you ingress account here https://intel.ingress.com/intel
2. Press F12 and go into Network tab , then press F5(refresh) to refresh browser and to reload all info in newtowrk tab then select intel in left coulumn and Headers in right, you should see *cookie* in **Request Headers**


![csrftoken-same-cookie](https://i.imgur.com/hyJ0ftT.jpg)




3. copy everything after **cookie:** and paste in Cookie section of default.ini


# Installation 
*pip install -r requirements.txt*

# config
for BBOX params in config file, go to http://bboxfinder.com and geofence your area you would like. once done it will give a rectangular shape for seleted area. copy whole line from after BBOX from the bottom panel)


![BBOX params](https://i.imgur.com/QKROPSU.jpg)

# Run
to update stops
**python scrape_portal.py -p**

to update gyms
**python scrape_portal.py -g**

to update ingress portals in manual DB
**python scrape_portal.py -i**

to update gyms and pokestops by geofence
**python scrape_portal.py -all -g -p**

to update gyms by geofence
**python scrape_portal.py -all -g**

to update pokestops by geofence
**python scrape_portal.py -all -p**
It should update names and url/image in rdm DB
