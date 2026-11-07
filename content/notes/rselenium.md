---
aliases:
  - /teaching/rvest-rselenium/
title: 'Using RSelenium to overcome rvest limitations'
date: 2017-10-22
tags: [R, web scraping]
---


## Rvest vs Rselenium

Its very often the case that data crawling needs to accomodate cookie requests from the website and/or by pass login authorizations. While rvest is a great tool to process html text, accomodating cookies and login requests can be quite troublesome.

The main problem comes with the internals of `read_html()` function which builds on `curl` type of requests. This connection is often stateless and may result to 301 http errors.

An easy way to overcome this, is to rely on the browser in order to capture the `html` part that we wish to parse. Therefore using `rselenium` is the most efficient way to address that, although it requires some effort to run.

## Prerequisites

To begin with you need a standalone version of a selenium server (you can download the latest version of selenium server from [here](https://goo.gl/21wWg8)

The second most important step is to download a browser extension to use with the selenium server. I strongly suggest chrome since this is the fastest and more convinient one. You can download the chrome webdriver extension for your platform from [here.](https://chromedriver.storage.googleapis.com/index.html?path=2.33/)

Once you have it downloaded and unziped it in the same folder assuming that your JRE works fine and you are in windows (for other platforms modify accordingly)

``` r
# Note that the -port defines the port that the server will run 
# the -D argument of the jar defines the web driver path 
# in our case is located on the folder chromedriver_win32 in the 
# same folder with the selenium server. The version of the selenium 
# server might change as well. 
java -Dwebdriver.chrome.driver=chromedriver_win32\chromedriver.exe -jar selenium-server-standalone-3.5.3.jar -port 4445
```

## Using Rselenium

``` r
#install the package if you don't allready have it
#install.packages("Rselenium")

#load the package
library(RSelenium)
library(rvest)

#Set to 2 if you don't want images to load 
prefs = list("profile.managed_default_content_settings.images" = 1L)
cprof <- list(chromeOptions = list(prefs = prefs))

#Open browser and navigate to login page
remDr <- remoteDriver(remoteServerAddr = "localhost",
                      extraCapabilities = cprof,
                      port = 4445L,
                      browserName = "chrome")

#Set to True if you want your browser to open in front of you
remDr$open(silent = F)
remDr$navigate("http://www.theurlofyourchoice.com")

this_page_src <- remDr$getPageSource()

# Use your rvest here to read the html code captured through Rselenium.

page_scr <- read_html(this_page_src)

# Do your rvest staf here 

page_src %>% 
   html_text()
```

