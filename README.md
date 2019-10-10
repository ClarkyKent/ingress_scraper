# ingress_scraper

original API by https://github.com/lc4t/ingress-api
since it was last modified in 2017, since URL of intel map has changed so installing ingressAPI via pip will install version that have old url. 


In order to make API work you need cookies from ingress's intel site. 
1. Log into you ingress account here https://intel.ingress.com/intel
2. Press F12 and go into Network tab and select Headers, you should see *cookie* in **Request Headers**


![csrftoken-same-cookie](https://ww4.sinaimg.cn/large/006tNbRwgw1farvqqqf7mj30r20vi12i.jpg)




3. copy everything after **cookie:** and paste in Cookie section of default.ini

if everything setup correctly, 
just run 
**python3 scrape_portal.py**

It should update names and url/image of gyms in rdm DB
