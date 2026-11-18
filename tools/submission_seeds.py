"""
Verified high-authority submission platforms, seeded per off-page SEO category.
DA values are NOT hardcoded guesses; live DA is fetched via Moz / Open PageRank APIs only.
Defunct and unreachable platforms have been removed; URLs point to active endpoints.
"""

SUBMISSION_PLATFORMS: dict = {
    "Blog Post Submission": {
        "icon": "📝",
        "description": "Publish articles and guest posts on high-authority blogging platforms to earn backlinks and traffic.",
        "task_type": "Content Publishing",
        "platforms": [
            {"name": "Medium", "domain": "medium.com", "url": "https://medium.com/", "cost": "100% Free", "action": "Write & Publish", "how_to_perform": "Sign up at medium.com, click 'Write a story', paste your article, add your website link in the body or bio, then publish."},
            {"name": "Substack", "domain": "substack.com", "url": "https://substack.com/", "cost": "100% Free", "action": "Create Newsletter", "how_to_perform": "Go to substack.com, create a free publication, write your post, include your site URL, and hit publish."},
            {"name": "LinkedIn Articles", "domain": "linkedin.com", "url": "https://www.linkedin.com/", "cost": "100% Free", "action": "Write Article", "how_to_perform": "Log in to LinkedIn, click 'Write article' from the home feed, compose your article with your site link, and publish."},
            {"name": "Vocal Media", "domain": "vocal.media", "url": "https://vocal.media/", "cost": "100% Free", "action": "Submit Story", "how_to_perform": "Register at vocal.media, click 'Create Story', write and include your link, then submit."},
            {"name": "Ghost", "domain": "ghost.org", "url": "https://ghost.org/", "cost": "100% Free", "action": "Publish Post", "how_to_perform": "Create a free publication on ghost.org, write your post with website links, and publish it publicly."},
            {"name": "Blogger", "domain": "blogger.com", "url": "https://www.blogger.com/", "cost": "100% Free", "action": "Publish Post", "how_to_perform": "Sign in with Google at blogger.com, create a blog, write your post with a backlink, and publish."},
            {"name": "WordPress.com", "domain": "wordpress.com", "url": "https://wordpress.com/", "cost": "100% Free", "action": "Publish Post", "how_to_perform": "Create a free site at wordpress.com, write your blog post with your URL, and publish."},
            {"name": "Tumblr", "domain": "tumblr.com", "url": "https://www.tumblr.com/", "cost": "100% Free", "action": "Create Post", "how_to_perform": "Register at tumblr.com, create a text post with your content and site URL, and share it."},
            {"name": "Dev.to", "domain": "dev.to", "url": "https://dev.to/", "cost": "100% Free", "action": "Publish Article", "how_to_perform": "Create an account at dev.to, write a technical or business article, include your website URL, and publish."},
            {"name": "Hashnode", "domain": "hashnode.com", "url": "https://hashnode.com/", "cost": "100% Free", "action": "Publish Article", "how_to_perform": "Sign up at hashnode.com, create your blog, write an article with your link, and post it."},
            {"name": "Wix Blog", "domain": "wix.com", "url": "https://www.wix.com/", "cost": "100% Free", "action": "Publish Blog", "how_to_perform": "Create a free Wix site, enable the Blog app, write a post with your website URL, and publish."},
            {"name": "Weebly", "domain": "weebly.com", "url": "https://www.weebly.com/", "cost": "100% Free", "action": "Publish Post", "how_to_perform": "Create a free site at weebly.com, use the blog section, write your post with your link, and publish."},
            {"name": "Penzu", "domain": "penzu.com", "url": "https://penzu.com/", "cost": "100% Free", "action": "Create Entry", "how_to_perform": "Sign up at penzu.com, write a journal/blog entry with your URL, and make it public."},
            {"name": "Write.as", "domain": "write.as", "url": "https://write.as/", "cost": "100% Free", "action": "Publish Story", "how_to_perform": "Visit write.as, compose a focused blog post with your website URL, and publish without friction."},
            {"name": "Tealfeed", "domain": "tealfeed.com", "url": "https://tealfeed.com/", "cost": "100% Free", "action": "Publish Article", "how_to_perform": "Join tealfeed.com, share insightful industry posts and case studies with backlink references."},
            {"name": "Steemit", "domain": "steemit.com", "url": "https://steemit.com/", "cost": "100% Free", "action": "Post Story", "how_to_perform": "Create a free Steemit account, post your article in relevant tags, and include your site link."},
            {"name": "Hive Blog", "domain": "hive.blog", "url": "https://hive.blog/", "cost": "100% Free", "action": "Publish Article", "how_to_perform": "Create an account on hive.blog, format your content in markdown, and share it with contextual links."},
            {"name": "Site123", "domain": "site123.com", "url": "https://www.site123.com/", "cost": "100% Free", "action": "Create Site & Blog", "how_to_perform": "Build a free one-page site or blog at site123.com, add relevant articles linking back to your domain."},
            {"name": "Jimdo", "domain": "jimdo.com", "url": "https://www.jimdo.com/", "cost": "100% Free", "action": "Create Website", "how_to_perform": "Sign up for a free Jimdo site, publish informative pages with your brand link."},
            {"name": "Strikingly", "domain": "strikingly.com", "url": "https://www.strikingly.com/", "cost": "100% Free", "action": "Create Landing Page", "how_to_perform": "Create a free landing page at strikingly.com featuring your business overview and website link."},
            {"name": "Webnode", "domain": "webnode.com", "url": "https://www.webnode.com/", "cost": "100% Free", "action": "Create Blog", "how_to_perform": "Sign up on webnode.com, choose a modern blog template, and write engaging articles with backlinks."},
            {"name": "Notion", "domain": "notion.so", "url": "https://www.notion.so/", "cost": "100% Free", "action": "Publish Public Page", "how_to_perform": "Draft helpful resource guides in Notion, click Share > Publish to web, and include direct links to your site."},
            {"name": "GitBook", "domain": "gitbook.com", "url": "https://www.gitbook.com/", "cost": "100% Free", "action": "Publish Docs", "how_to_perform": "Create a public GitBook documentation or knowledge base space and link back to your primary services."},
            {"name": "OverBlog", "domain": "over-blog.com", "url": "https://www.over-blog.com/", "cost": "100% Free", "action": "Create Blog", "how_to_perform": "Register at over-blog.com, publish content in your niche, and add links back to your website."},
            {"name": "Svbtle", "domain": "svbtle.com", "url": "https://svbtle.com/", "cost": "100% Free", "action": "Publish Post", "how_to_perform": "Create a clean, minimalist publication on svbtle.com and share thought-leadership posts with your URL."}
        ],
    },

    "PR Submission": {
        "icon": "📣",
        "description": "Distribute press releases to high-DA news and PR sites for brand visibility and authority backlinks.",
        "task_type": "Press Release",
        "platforms": [
            {"name": "PRLog", "domain": "prlog.org", "url": "https://www.prlog.org/", "cost": "100% Free", "action": "Submit PR", "how_to_perform": "Go to prlog.org, click 'Submit Free Press Release', fill in headline, body with your URL, and submit."},
            {"name": "PR.com", "domain": "pr.com", "url": "https://www.pr.com/", "cost": "100% Free", "action": "Submit PR", "how_to_perform": "Register at pr.com, navigate to submit news, fill in all fields with your website URL, and publish."},
            {"name": "OpenPR", "domain": "openpr.com", "url": "https://www.openpr.com/", "cost": "100% Free", "action": "Submit PR", "how_to_perform": "Sign up at openpr.com, click Submit Press Release, enter your news with your site URL, and publish free."},
            {"name": "PRFree", "domain": "prfree.org", "url": "https://www.prfree.org/", "cost": "100% Free", "action": "Submit PR", "how_to_perform": "Go to prfree.org, click 'Submit a Press Release', write your PR with website URL, and submit."},
            {"name": "1888PressRelease", "domain": "1888pressrelease.com", "url": "https://www.1888pressrelease.com/", "cost": "100% Free", "action": "Submit PR", "how_to_perform": "Register at 1888pressrelease.com, submit your press release with your website link included."},
            {"name": "IssueWire", "domain": "issuewire.com", "url": "https://www.issuewire.com/", "cost": "100% Free", "action": "Submit PR", "how_to_perform": "Register at issuewire.com, go to Submit Press Release, fill in details including your website URL."},
            {"name": "Newswire", "domain": "newswire.com", "url": "https://www.newswire.com/", "cost": "Paid/Free Trial", "action": "Distribute PR", "how_to_perform": "Create an account on newswire.com, choose release format, embed your company URL, and schedule distribution."},
            {"name": "EIN Presswire", "domain": "einpresswire.com", "url": "https://www.einpresswire.com/", "cost": "Paid/Free Trial", "action": "Submit PR", "how_to_perform": "Sign up at einpresswire.com, upload your industry news announcement, and include backlinks to your domain."},
            {"name": "Pressat", "domain": "pressat.co.uk", "url": "https://pressat.co.uk/", "cost": "Paid/Free Trial", "action": "Distribute PR", "how_to_perform": "Register on pressat.co.uk, submit your company milestone, and distribute to relevant UK and international desks."},
            {"name": "OnlinePRNews", "domain": "onlineprnews.com", "url": "https://www.onlineprnews.com/", "cost": "100% Free", "action": "Submit PR", "how_to_perform": "Create an account on onlineprnews.com, select the free tier, and submit your announcement."},
            {"name": "Express Press Release", "domain": "express-press-release.net", "url": "https://express-press-release.net/", "cost": "100% Free", "action": "Submit PR", "how_to_perform": "Visit express-press-release.net, enter your business press release, and submit for distribution."},
            {"name": "PR Underground", "domain": "prounderground.com", "url": "https://www.prounderground.com/", "cost": "Paid", "action": "Submit PR", "how_to_perform": "Submit on prounderground.com for Google News and social syndication of your announcements."},
            {"name": "BusinessWire", "domain": "businesswire.com", "url": "https://www.businesswire.com/", "cost": "Paid", "action": "Submit PR", "how_to_perform": "Go to businesswire.com, create an enterprise account, and submit tier-1 press releases."},
            {"name": "PRNewswire", "domain": "prnewswire.com", "url": "https://www.prnewswire.com/", "cost": "Paid", "action": "Submit PR", "how_to_perform": "Register at prnewswire.com, select your distribution package, and submit releases with your URL."},
            {"name": "GlobeNewswire", "domain": "globenewswire.com", "url": "https://www.globenewswire.com/", "cost": "Paid", "action": "Submit PR", "how_to_perform": "Sign up at globenewswire.com, select a package, and submit your news with your website link."},
            {"name": "WebWire", "domain": "webwire.com", "url": "https://www.webwire.com/", "cost": "Paid/Free Trial", "action": "Submit Release", "how_to_perform": "Sign up at webwire.com, format your news release with your company URL, and submit for editorial review."},
            {"name": "24-7 Press Release", "domain": "24-7pressrelease.com", "url": "https://www.24-7pressrelease.com/", "cost": "Paid/Free Trial", "action": "Submit PR", "how_to_perform": "Create an account on 24-7pressrelease.com, select your industry category, and post your company news."}
        ],
    },

    "Profile Creation": {
        "icon": "👤",
        "description": "Build authoritative business profiles on high-DA platforms to create strong branded backlinks.",
        "task_type": "Profile Building",
        "platforms": [
            {"name": "Crunchbase", "domain": "crunchbase.com", "url": "https://www.crunchbase.com/", "cost": "100% Free", "action": "Create Profile", "how_to_perform": "Go to crunchbase.com, sign up, click 'Add a Company', fill in your business details including your website URL, and submit."},
            {"name": "AngelList (Wellfound)", "domain": "wellfound.com", "url": "https://we llfound.com/", "cost": "100% Free", "action": "Create Profile", "how_to_perform": "Register at wellfound.com, create a company profile, add your website URL and business details."},
            {"name": "About.me", "domain": "about.me", "url": "https://about.me/", "cost": "100% Free", "action": "Create Profile", "how_to_perform": "Go to about.me, sign up, build your personal/brand profile, add your website URL prominently."},
            {"name": "Gravatar", "domain": "gravatar.com", "url": "https://gravatar.com/", "cost": "100% Free", "action": "Create Profile", "how_to_perform": "Go to gravatar.com, sign in with WordPress.com, upload your photo, and add your website URL to your profile."},
            {"name": "Manta", "domain": "manta.com", "url": "https://www.manta.com/", "cost": "100% Free", "action": "Create Business Profile", "how_to_perform": "Go to manta.com, search for your business to claim it or add new, complete your profile with website URL."},
            {"name": "Behance", "domain": "behance.net", "url": "https://www.behance.net/", "cost": "100% Free", "action": "Create Portfolio", "how_to_perform": "Sign up at behance.net with Adobe account, create a profile, link your website in the profile section."},
            {"name": "Dribbble", "domain": "dribbble.com", "url": "https://dribbble.com/", "cost": "100% Free", "action": "Create Profile", "how_to_perform": "Register at dribbble.com, set up your profile with your website URL in the bio section."},
            {"name": "Product Hunt", "domain": "producthunt.com", "url": "https://www.producthunt.com/", "cost": "100% Free", "action": "Launch Product", "how_to_perform": "Register at producthunt.com, submit your product/business with a full description and your website URL."},
            {"name": "Yelp for Business", "domain": "yelp.com", "url": "https://biz.yelp.com/", "cost": "100% Free", "action": "Claim Business", "how_to_perform": "Go to biz.yelp.com, search for your business (or add new), complete the profile including your website URL."},
            {"name": "Foursquare", "domain": "foursquare.com", "url": "https://foursquare.com/", "cost": "100% Free", "action": "Claim Venue", "how_to_perform": "Visit foursquare.com, search for your business or add it, complete profile with website URL."},
            {"name": "Hotfrog", "domain": "hotfrog.com", "url": "https://www.hotfrog.com/", "cost": "100% Free", "action": "Add Business", "how_to_perform": "Go to hotfrog.com, click 'Add your business', fill in business name, category, website URL, and submit."},
            {"name": "Cylex", "domain": "cylex.us.com", "url": "https://www.cylex.us.com/", "cost": "100% Free", "action": "Create Profile", "how_to_perform": "Register at cylex.us.com, add your business profile with website URL and contact details."},
            {"name": "GitHub", "domain": "github.com", "url": "https://github.com/", "cost": "100% Free", "action": "Create Org Profile", "how_to_perform": "Sign up on github.com, create a brand organisation, add your website URL and social links in the bio."},
            {"name": "GitLab", "domain": "gitlab.com", "url": "https://gitlab.com/", "cost": "100% Free", "action": "Create Profile", "how_to_perform": "Register at gitlab.com, set up a public profile with company description and link."},
            {"name": "SourceForge", "domain": "sourceforge.net", "url": "https://sourceforge.net/", "cost": "100% Free", "action": "Create Profile", "how_to_perform": "Create a developer or organization account on sourceforge.net with your homepage link."},
            {"name": "TED Community", "domain": "ted.com", "url": "https://www.ted.com/", "cost": "100% Free", "action": "Create Profile", "how_to_perform": "Register on ted.com, fill out your public member profile, and link to your business site."},
            {"name": "Linktree", "domain": "linktr.ee", "url": "https://linktr.ee/", "cost": "100% Free", "action": "Create Bio Page", "how_to_perform": "Sign up at linktr.ee, create a centralized hub linking back to your main site and services."},
            {"name": "Carrd", "domain": "carrd.co", "url": "https://carrd.co/", "cost": "100% Free", "action": "Build Profile", "how_to_perform": "Build a responsive one-page profile on carrd.co directing visitors to your primary website."},
            {"name": "Bento", "domain": "bento.me", "url": "https://bento.me/", "cost": "100% Free", "action": "Create Bento Profile", "how_to_perform": "Create a rich visual profile on bento.me with custom widgets pointing to your site."},
            {"name": "Bio.link", "domain": "bio.link", "url": "https://bio.link/", "cost": "100% Free", "action": "Create Bio Link", "how_to_perform": "Set up a clean bio.link landing page with prominent backlinks to your properties."},
            {"name": "GoodFirms", "domain": "goodfirms.co", "url": "https://www.goodfirms.co/", "cost": "100% Free", "action": "List Company", "how_to_perform": "Register your business on goodfirms.co, select services, and add verified website links."},
            {"name": "Clutch", "domain": "clutch.co", "url": "https://clutch.co/", "cost": "100% Free", "action": "Create Agency Profile", "how_to_perform": "List your business on clutch.co, complete client work descriptions, and link your domain."}
        ],
    },

    "Business Listing": {
        "icon": "🏢",
        "description": "Submit your business to authoritative directories to build citations, trust, and local SEO signals.",
        "task_type": "Directory Submission",
        "platforms": [
            {"name": "Google Business Profile", "domain": "business.google.com", "url": "https://business.google.com/", "cost": "100% Free", "action": "Claim/Create Listing", "how_to_perform": "Go to business.google.com, sign in with Google, search for your business or add it, complete all fields including website URL, and verify."},
            {"name": "Bing Places", "domain": "bingplaces.com", "url": "https://www.bingplaces.com/", "cost": "100% Free", "action": "Add Business", "how_to_perform": "Go to bingplaces.com, sign in with Microsoft, add or claim your business, complete the profile with your website."},
            {"name": "Apple Maps Connect", "domain": "mapsconnect.apple.com", "url": "https://mapsconnect.apple.com/", "cost": "100% Free", "action": "Add Business", "how_to_perform": "Go to mapsconnect.apple.com, sign in with Apple ID, add your business details and website URL."},
            {"name": "Yellow Pages", "domain": "yellowpages.com", "url": "https://www.yellowpages.com/", "cost": "100% Free", "action": "Add Listing", "how_to_perform": "Go to yellowpages.com, click 'Add your business free', fill in business details including your website URL, and verify."},
            {"name": "BBB (Better Business Bureau)", "domain": "bbb.org", "url": "https://www.bbb.org/", "cost": "100% Free", "action": "Accreditation Application", "how_to_perform": "Go to bbb.org, click 'For Businesses', apply for accreditation or free business listing with your website URL."},
            {"name": "Superpages", "domain": "superpages.com", "url": "https://www.superpages.com/", "cost": "100% Free", "action": "Add Listing", "how_to_perform": "Go to superpages.com, click 'Add your business', complete the form with your website URL."},
            {"name": "Brownbook", "domain": "brownbook.net", "url": "https://www.brownbook.net/", "cost": "100% Free", "action": "Add Business", "how_to_perform": "Register at brownbook.net, click 'Add a Business', fill in details including your website URL."},
            {"name": "EZlocal", "domain": "ezlocal.com", "url": "https://ezlocal.com/", "cost": "100% Free", "action": "Add Business", "how_to_perform": "Go to ezlocal.com, click 'Add your business', fill in all details with your website URL and submit."},
            {"name": "Alignable", "domain": "alignable.com", "url": "https://www.alignable.com/", "cost": "100% Free", "action": "Create Profile", "how_to_perform": "Register at alignable.com, build your business profile including your website URL."},
            {"name": "Thumbtack", "domain": "thumbtack.com", "url": "https://www.thumbtack.com/", "cost": "100% Free", "action": "Create Profile", "how_to_perform": "Register at thumbtack.com as a pro, create a service profile including your website URL."},
            {"name": "Sitejabber", "domain": "sitejabber.com", "url": "https://www.sitejabber.com/", "cost": "100% Free", "action": "Claim Business", "how_to_perform": "Go to sitejabber.com, search for your business, claim it, and add your website URL to the profile."},
            {"name": "Dun & Bradstreet", "domain": "dnb.com", "url": "https://www.dnb.com/", "cost": "100% Free", "action": "Register Business", "how_to_perform": "Visit dnb.com, register your business to get a DUNS number and create your free business listing with website URL."},
            {"name": "Chamber of Commerce", "domain": "chamberofcommerce.com", "url": "https://www.chamberofcommerce.com/", "cost": "100% Free", "action": "Add Directory Listing", "how_to_perform": "Add your company profile on chamberofcommerce.com with complete NAP data and website link."},
            {"name": "MerchantCircle", "domain": "merchantcircle.com", "url": "https://www.merchantcircle.com/", "cost": "100% Free", "action": "Claim Listing", "how_to_perform": "Join merchantcircle.com, claim your local listing, and post business updates with your link."},
            {"name": "ShowMeLocal", "domain": "showmelocal.com", "url": "https://www.showmelocal.com/", "cost": "100% Free", "action": "Add Business", "how_to_perform": "Register on showmelocal.com, submit your address, opening hours, and official website URL."},
            {"name": "CitySquares", "domain": "citysquares.com", "url": "https://citysquares.com/", "cost": "100% Free", "action": "Add Listing", "how_to_perform": "Submit your neighborhood business listing on citysquares.com with accurate backlink data."},
            {"name": "Tupalo", "domain": "tupalo.com", "url": "https://tupalo.com/", "cost": "100% Free", "action": "Add Spot", "how_to_perform": "Register on tupalo.com, list your business spot, and link to your homepage."},
            {"name": "Yalwa", "domain": "yalwa.com", "url": "https://www.yalwa.com/", "cost": "100% Free", "action": "Post Free Listing", "how_to_perform": "Post your local service on yalwa.com in your country and city category."},
            {"name": "Cybo", "domain": "cybo.com", "url": "https://www.cybo.com/", "cost": "100% Free", "action": "Claim Company", "how_to_perform": "Search for your enterprise on cybo.com, claim the profile, and verify website information."},
            {"name": "LocalStack", "domain": "localstack.com", "url": "https://localstack.com/", "cost": "100% Free", "action": "Add Business", "how_to_perform": "List your business profile and location on localstack.com with category tags."}
        ],
    },
    

    "Map Citation": {
        "icon": "📍",
        "description": "Add your business location to map and local citation sites to boost local SEO authority.",
        "task_type": "Local Citation",
        "platforms": [
            {"name": "Google Maps", "domain": "maps.google.com", "url": "https://business.google.com/", "cost": "100% Free", "action": "Add/Claim Location", "how_to_perform": "Go to business.google.com, add or claim your business, add your exact address, phone, website URL, and verify by postcard or phone."},
            {"name": "Bing Maps", "domain": "bing.com", "url": "https://www.bingplaces.com/", "cost": "100% Free", "action": "Add Location", "how_to_perform": "Visit bingplaces.com, sign in, add your business with address and website URL."},
            {"name": "OpenStreetMap", "domain": "openstreetmap.org", "url": "https://www.openstreetmap.org/", "cost": "100% Free", "action": "Add Node/Way", "how_to_perform": "Create an account at openstreetmap.org, use the editor to add your business location, name, and website URL as a tag."},
            {"name": "Waze", "domain": "waze.com", "url": "https://www.waze.com/business", "cost": "100% Free", "action": "Add Place", "how_to_perform": "Go to waze.com/business, add your location or claim your existing place, add website URL."},
            {"name": "MapQuest", "domain": "mapquest.com", "url": "https://www.mapquest.com/", "cost": "100% Free", "action": "Add Listing", "how_to_perform": "Go to mapquest.com, add your business listing with address and website URL."},
            {"name": "HERE Maps", "domain": "here.com", "url": "https://mapcreator.here.com/", "cost": "100% Free", "action": "Submit Location", "how_to_perform": "Go to mapcreator.here.com, sign in, and add your business location with website URL."},
            {"name": "TomTom", "domain": "tomtom.com", "url": "https://www.tomtom.com/", "cost": "100% Free", "action": "Submit Location", "how_to_perform": "Go to tomtom.com, access map updates to add or correct your business location."},
            {"name": "Foursquare City Guide", "domain": "foursquare.com", "url": "https://foursquare.com/", "cost": "100% Free", "action": "Add Venue", "how_to_perform": "Sign up at foursquare.com, add your venue with full address and website URL."},
            {"name": "Yext", "domain": "yext.com", "url": "https://www.yext.com/", "cost": "Paid/Free Trial", "action": "Manage Listings", "how_to_perform": "Sign up at yext.com, use their platform to distribute your business info (including website URL) across 100+ directories."},
            {"name": "Apple Maps", "domain": "apple.com", "url": "https://mapsconnect.apple.com/", "cost": "100% Free", "action": "Add Apple Map Place", "how_to_perform": "Log in to Apple Maps Connect with your Apple ID and verify your physical business location."},
            {"name": "Navmii", "domain": "navmii.com", "url": "https://navmii.com/", "cost": "100% Free", "action": "Add POI", "how_to_perform": "Submit point of interest (POI) information to Navmii navigation services with your URL."},
            {"name": "Mapbox", "domain": "mapbox.com", "url": "https://www.mapbox.com/", "cost": "100% Free", "action": "Contribute Data", "how_to_perform": "Contribute geospatial venue data via Mapbox developer tools and OpenStreetMap integration."}
        ],
    },

    "Classified Ads": {
        "icon": "📋",
        "description": "Post free classified ads to drive traffic and create backlinks from high-authority listing sites.",
        "task_type": "Classified Submission",
        "platforms": [
            {"name": "Craigslist", "domain": "craigslist.org", "url": "https://www.craigslist.org/", "cost": "100% Free", "action": "Post Ad", "how_to_perform": "Go to craigslist.org, select your city/region, click 'Post to Classifieds', choose category, write your ad with website URL, and submit."},
            {"name": "Gumtree", "domain": "gumtree.com", "url": "https://www.gumtree.com/", "cost": "100% Free", "action": "Post Ad", "how_to_perform": "Register at gumtree.com, click 'Place an ad', fill in your ad details with a link to your website, and post."},
            {"name": "OLX", "domain": "olx.com", "url": "https://www.olx.com/", "cost": "100% Free", "action": "Post Ad", "how_to_perform": "Register at olx.com (use your country's version), click 'Post an Ad', fill in details including website URL."},
            {"name": "Locanto", "domain": "locanto.com", "url": "https://www.locanto.com/", "cost": "100% Free", "action": "Post Ad", "how_to_perform": "Go to locanto.com, select your city, click 'Place ad for free', fill in details with your website link."},
            {"name": "Hoobly", "domain": "hoobly.com", "url": "https://www.hoobly.com/", "cost": "100% Free", "action": "Post Ad", "how_to_perform": "Register at hoobly.com, click 'Post Ad', fill in the category and your ad content with website URL."},
            {"name": "Classifiedads.com", "domain": "classifiedads.com", "url": "https://www.classifiedads.com/", "cost": "100% Free", "action": "Post Ad", "how_to_perform": "Go to classifiedads.com, register, choose your category, write your ad with your website URL, and post."},
            {"name": "Oodle", "domain": "oodle.com", "url": "https://www.oodle.com/", "cost": "100% Free", "action": "Post Ad", "how_to_perform": "Register at oodle.com, post a classified ad in the relevant category with your website URL."},
            {"name": "Geebo", "domain": "geebo.com", "url": "https://geebo.com/", "cost": "100% Free", "action": "Post Ad", "how_to_perform": "Go to geebo.com, click 'Post an Ad', select your category, write your ad with your website link."},
            {"name": "Adlandpro", "domain": "adlandpro.com", "url": "https://www.adlandpro.com/", "cost": "100% Free", "action": "Post Ad", "how_to_perform": "Register at adlandpro.com, go to Post Free Ads, fill in your ad description with website URL."},
            {"name": "FreeAds", "domain": "freeads.co.uk", "url": "https://www.freeads.co.uk/", "cost": "100% Free", "action": "Place Ad", "how_to_perform": "Sign up on freeads.co.uk, select category, and publish ads including your website link."},
            {"name": "Adpost", "domain": "adpost.com", "url": "https://www.adpost.com/", "cost": "100% Free", "action": "Post Free Ad", "how_to_perform": "Submit targeted classifieds across global regional sections on adpost.com."},
            {"name": "USFreeAds", "domain": "usfreeads.com", "url": "https://www.usfreeads.com/", "cost": "100% Free", "action": "Post Listing", "how_to_perform": "Create free classified advertisements with live website anchors on usfreeads.com."}
        ],
    },

    "PPT / Video Submission": {
        "icon": "🎬",
        "description": "Share presentations and videos on authority platforms to build backlinks and brand awareness.",
        "task_type": "Media Submission",
        "platforms": [
            {"name": "SlideShare", "domain": "slideshare.net", "url": "https://www.slideshare.net/", "cost": "100% Free", "action": "Upload Presentation", "how_to_perform": "Sign in at slideshare.net with LinkedIn, click Upload, upload your PPT/PDF, add description with your website URL, and publish."},
            {"name": "YouTube", "domain": "youtube.com", "url": "https://www.youtube.com/", "cost": "100% Free", "action": "Upload Video", "how_to_perform": "Sign in to YouTube with Google, click '+' > 'Upload video', upload your video, add description with website URL, and publish."},
            {"name": "Vimeo", "domain": "vimeo.com", "url": "https://vimeo.com/", "cost": "100% Free", "action": "Upload Video", "how_to_perform": "Register at vimeo.com, click 'Upload', add your video, include website URL in the description, and publish."},
            {"name": "Speaker Deck", "domain": "speakerdeck.com", "url": "https://speakerdeck.com/", "cost": "100% Free", "action": "Upload Slides", "how_to_perform": "Sign up at speakerdeck.com, click 'Upload', upload your presentation PDF, add description with your website URL."},
            {"name": "Scribd", "domain": "scribd.com", "url": "https://www.scribd.com/", "cost": "100% Free", "action": "Upload Document", "how_to_perform": "Register at scribd.com, click 'Upload', upload your document/PPT with your website URL in the content."},
            {"name": "SlideServe", "domain": "slideserve.com", "url": "https://www.slideserve.com/", "cost": "100% Free", "action": "Upload Slides", "how_to_perform": "Register at slideserve.com, click 'Upload Presentation', upload your file, add your website URL in the description."},
            {"name": "Issuu", "domain": "issuu.com", "url": "https://issuu.com/", "cost": "100% Free", "action": "Upload Publication", "how_to_perform": "Sign up at issuu.com, click 'Upload', upload your document, add your website URL in the publication details."},
            {"name": "Dailymotion", "domain": "dailymotion.com", "url": "https://www.dailymotion.com/", "cost": "100% Free", "action": "Upload Video", "how_to_perform": "Create an account at dailymotion.com, upload your video, include your website URL in the description."},
            {"name": "Internet Archive", "domain": "archive.org", "url": "https://archive.org/", "cost": "100% Free", "action": "Upload Media", "how_to_perform": "Create an account on archive.org, upload educational whitepapers or video guides with link references."},
            {"name": "DocDroid", "domain": "docdroid.net", "url": "https://www.docdroid.net/", "cost": "100% Free", "action": "Upload PDF", "how_to_perform": "Upload public brochures or presentation PDFs to docdroid.net with clickable links."},
            {"name": "Calameo", "domain": "calameo.com", "url": "https://www.calameo.com/", "cost": "100% Free", "action": "Publish Document", "how_to_perform": "Publish digital magazines and company presentations on calameo.com with backlinks."},
            {"name": "Edocr", "domain": "edocr.com", "url": "https://www.edocr.com/", "cost": "100% Free", "action": "Upload Document", "how_to_perform": "Distribute whitepapers on edocr.com for lead generation and backlink attribution."}
        ],
    },

    "Infographic Submission": {
        "icon": "📊",
        "description": "Submit infographics to visual content directories for backlinks and viral sharing potential.",
        "task_type": "Visual Content Submission",
        "platforms": [
            {"name": "Visual.ly", "domain": "visual.ly", "url": "https://visual.ly/", "cost": "100% Free", "action": "Submit Infographic", "how_to_perform": "Register at visual.ly, click 'Submit', upload your infographic image, add your website URL as the source link."},
            {"name": "Infogram", "domain": "infogram.com", "url": "https://infogram.com/", "cost": "100% Free", "action": "Create & Share", "how_to_perform": "Sign up at infogram.com, create or upload your infographic, publish publicly, and add your website URL."},
            {"name": "Venngage", "domain": "venngage.com", "url": "https://venngage.com/", "cost": "100% Free", "action": "Create & Publish", "how_to_perform": "Register at venngage.com, create your infographic, publish it publicly, and include your website URL."},
            {"name": "Canva", "domain": "canva.com", "url": "https://www.canva.com/", "cost": "100% Free", "action": "Publish Design", "how_to_perform": "Create your infographic on canva.com, click Share > Publish to Web, add your website URL in the design."},
            {"name": "Piktochart", "domain": "piktochart.com", "url": "https://piktochart.com/", "cost": "100% Free", "action": "Publish Infographic", "how_to_perform": "Sign up at piktochart.com, design your infographic, make it public, and add your site URL."},
            {"name": "Reddit (r/infographics)", "domain": "reddit.com", "url": "https://www.reddit.com/r/infographics/", "cost": "100% Free", "action": "Submit Post", "how_to_perform": "Log in to Reddit, go to r/infographics, click 'Create Post', submit your infographic image with your website URL in the comments."},
            {"name": "Pinterest", "domain": "pinterest.com", "url": "https://www.pinterest.com/", "cost": "100% Free", "action": "Create Pin", "how_to_perform": "Create a Pinterest account, click '+' > 'Create Pin', upload your infographic, add your website URL as the destination link."},
            {"name": "Flickr", "domain": "flickr.com", "url": "https://www.flickr.com/", "cost": "100% Free", "action": "Upload Image", "how_to_perform": "Create a Flickr account, upload your infographic, add description with your website URL, set visibility to public."},
            {"name": "Graphs.net", "domain": "graphs.net", "url": "https://graphs.net/", "cost": "100% Free", "action": "Submit Infographic", "how_to_perform": "Submit your custom data visualization on graphs.net with backlink to your main article."},
            {"name": "Infographic Journal", "domain": "infographicjournal.com", "url": "https://infographicjournal.com/", "cost": "100% Free", "action": "Submit Graphic", "how_to_perform": "Register on infographicjournal.com and submit your infographic with original source citation."},
            {"name": "Visualistan", "domain": "visualistan.com", "url": "https://www.visualistan.com/", "cost": "100% Free", "action": "Submit Visuals", "how_to_perform": "Submit infographics and informative charts on visualistan.com with link back to your study."},
            {"name": "Visme", "domain": "visme.co", "url": "https://www.visme.co/", "cost": "100% Free", "action": "Publish Graphic", "how_to_perform": "Create interactive charts on visme.co and publish publicly with website link embeds."}
        ],
    },

    "Image Submission": {
        "icon": "🖼️",
        "description": "Share high-quality images on photo-sharing platforms to build backlinks and brand exposure.",
        "task_type": "Image Sharing",
        "platforms": [
            {"name": "Flickr", "domain": "flickr.com", "url": "https://www.flickr.com/", "cost": "100% Free", "action": "Upload Image", "how_to_perform": "Register at flickr.com, upload your images, add description with website URL, set to public."},
            {"name": "500px", "domain": "500px.com", "url": "https://500px.com/", "cost": "100% Free", "action": "Upload Photo", "how_to_perform": "Create an account at 500px.com, upload your image, add description with your website URL."},
            {"name": "Imgur", "domain": "imgur.com", "url": "https://imgur.com/", "cost": "100% Free", "action": "Upload Image", "how_to_perform": "Sign up at imgur.com, click 'New Post', upload your image, add description with website URL, and share."},
            {"name": "DeviantArt", "domain": "deviantart.com", "url": "https://www.deviantart.com/", "cost": "100% Free", "action": "Submit Artwork", "how_to_perform": "Register at deviantart.com, click 'Submit', upload your image, add description with website URL."},
            {"name": "Unsplash", "domain": "unsplash.com", "url": "https://unsplash.com/", "cost": "100% Free", "action": "Submit Photo", "how_to_perform": "Apply as a contributor at unsplash.com, upload your photos, and link back to your website in your profile."},
            {"name": "Smugmug", "domain": "smugmug.com", "url": "https://www.smugmug.com/", "cost": "100% Free", "action": "Upload Gallery", "how_to_perform": "Sign up at smugmug.com, upload your images, add your website URL in the bio and photo descriptions."},
            {"name": "Google Photos", "domain": "photos.google.com", "url": "https://photos.google.com/", "cost": "100% Free", "action": "Create Shared Album", "how_to_perform": "Use Google Photos, create a shared album, share the public link and include your website URL in descriptions."},
            {"name": "Photobucket", "domain": "photobucket.com", "url": "https://photobucket.com/", "cost": "100% Free", "action": "Upload Image", "how_to_perform": "Register at photobucket.com, upload your images, add your website URL in the description."},
            {"name": "Pexels", "domain": "pexels.com", "url": "https://www.pexels.com/", "cost": "100% Free", "action": "Contribute Photo", "how_to_perform": "Join pexels.com as a creator, upload high-res images, and add your business URL to your bio."},
            {"name": "Pixabay", "domain": "pixabay.com", "url": "https://pixabay.com/", "cost": "100% Free", "action": "Submit Media", "how_to_perform": "Register on pixabay.com, upload quality photography, and include your domain link in your creator profile."},
            {"name": "ArtStation", "domain": "artstation.com", "url": "https://www.artstation.com/", "cost": "100% Free", "action": "Publish Portfolio", "how_to_perform": "Create an ArtStation portfolio profile with links to your official website."}
        ],
    },

    "Micro Blog Submission": {
        "icon": "🐦",
        "description": "Publish micro-content on high-DA web 2.0 platforms for diverse backlink profiles.",
        "task_type": "Web 2.0 Submission",
        "platforms": [
            {"name": "Tumblr", "domain": "tumblr.com", "url": "https://www.tumblr.com/", "cost": "100% Free", "action": "Create Blog Post", "how_to_perform": "Register at tumblr.com, create a blog, write a text post with your website URL, and publish."},
            {"name": "WordPress.com", "domain": "wordpress.com", "url": "https://wordpress.com/", "cost": "100% Free", "action": "Create Blog", "how_to_perform": "Create a free blog at wordpress.com, write posts about your niche, include backlinks to your website."},
            {"name": "Blogger", "domain": "blogger.com", "url": "https://www.blogger.com/", "cost": "100% Free", "action": "Create Blog", "how_to_perform": "Sign in at blogger.com with Google, create a new blog, write posts with backlinks to your website."},
            {"name": "Weebly", "domain": "weebly.com", "url": "https://www.weebly.com/", "cost": "100% Free", "action": "Create Site", "how_to_perform": "Register at weebly.com, create a free website/blog, write content with links back to your main site."},
            {"name": "Wix", "domain": "wix.com", "url": "https://www.wix.com/", "cost": "100% Free", "action": "Create Blog", "how_to_perform": "Create a free Wix site at wix.com, enable the Blog feature, write posts linking back to your website."},
            {"name": "Livejournal", "domain": "livejournal.com", "url": "https://www.livejournal.com/", "cost": "100% Free", "action": "Create Blog", "how_to_perform": "Register at livejournal.com, create a blog, write posts with your website URL included."},
            {"name": "Typepad", "domain": "typepad.com", "url": "https://www.typepad.com/", "cost": "100% Free", "action": "Create Blog", "how_to_perform": "Sign up at typepad.com, create a free blog, publish posts with your website link."},
            {"name": "Substack Notes", "domain": "substack.com", "url": "https://substack.com/", "cost": "100% Free", "action": "Post Note", "how_to_perform": "Publish concise commentary and quick insights on Substack Notes referencing your site."},
            {"name": "Threads", "domain": "threads.net", "url": "https://www.threads.net/", "cost": "100% Free", "action": "Publish Thread", "how_to_perform": "Post topical microblog threads on Threads linking back to your authoritative articles."},
            {"name": "Bluesky", "domain": "bsky.app", "url": "https://bsky.app/", "cost": "100% Free", "action": "Post Update", "how_to_perform": "Share industry updates and helpful links on Bluesky to engage niche tech and business communities."},
            {"name": "Mastodon", "domain": "mastodon.social", "url": "https://mastodon.social/", "cost": "100% Free", "action": "Post Toot", "how_to_perform": "Create a verified profile on Mastodon with rel=me metadata pointing to your domain."},
            {"name": "Micro.blog", "domain": "micro.blog", "url": "https://micro.blog/", "cost": "100% Free", "action": "Publish Post", "how_to_perform": "Publish short-form thoughts and syndication links on micro.blog."}
        ],
    },

    "Blog Promotion": {
        "icon": "📢",
        "description": "Promote blog content on content curation and syndication platforms for more reach and backlinks.",
        "task_type": "Content Promotion",
        "platforms": [
            {"name": "Mix", "domain": "mix.com", "url": "https://mix.com/", "cost": "100% Free", "action": "Submit URL", "how_to_perform": "Register at mix.com, click the '+' button, enter your blog post URL, add tags, and submit to collections."},
            {"name": "Flipboard", "domain": "flipboard.com", "url": "https://flipboard.com/", "cost": "100% Free", "action": "Create Magazine", "how_to_perform": "Register at flipboard.com, create a magazine in your niche, flip/add your blog posts including website URL."},
            {"name": "Scoop.it", "domain": "scoop.it", "url": "https://www.scoop.it/", "cost": "100% Free", "action": "Curate Content", "how_to_perform": "Sign up at scoop.it, create a topic page, add your blog post URL as a scoop with a custom description."},
            {"name": "Reddit", "domain": "reddit.com", "url": "https://www.reddit.com/", "cost": "100% Free", "action": "Submit Link", "how_to_perform": "Log in to Reddit, find relevant subreddits for your niche, click 'Create Post', submit your blog URL (link post), and engage in comments."},
            {"name": "Hacker News", "domain": "news.ycombinator.com", "url": "https://news.ycombinator.com/submit", "cost": "100% Free", "action": "Submit Story", "how_to_perform": "Create an account on news.ycombinator.com, go to Submit, enter your blog post URL and title, and submit."},
            {"name": "Digg", "domain": "digg.com", "url": "https://digg.com/", "cost": "100% Free", "action": "Submit Story", "how_to_perform": "Register at digg.com, submit your blog post URL with a short description."},
            {"name": "Quuu Promote", "domain": "quuu.co", "url": "https://quuu.co/", "cost": "Paid/Free Trial", "action": "Promote Content", "how_to_perform": "Sign up at quuu.co, submit your blog post URL for promotion to social media influencers."},
            {"name": "Bizsugar", "domain": "bizsugar.com", "url": "https://bizsugar.com/", "cost": "100% Free", "action": "Submit Post", "how_to_perform": "Register at bizsugar.com, click 'Add a story', enter your blog post URL, description, and submit."},
            {"name": "GrowthHackers", "domain": "growthhackers.com", "url": "https://growthhackers.com/", "cost": "100% Free", "action": "Submit Article", "how_to_perform": "Join growthhackers.com, click '+', submit your article URL and description to the community."},
            {"name": "Pearltrees", "domain": "pearltrees.com", "url": "https://www.pearltrees.com/", "cost": "100% Free", "action": "Add Web Pearl", "how_to_perform": "Create collections on pearltrees.com and add direct bookmarks to your articles."},
            {"name": "Raindrop.io", "domain": "raindrop.io", "url": "https://raindrop.io/", "cost": "100% Free", "action": "Publish Collection", "how_to_perform": "Create public curated bookmark collections on raindrop.io featuring your content."},
            {"name": "Diigo", "domain": "diigo.com", "url": "https://www.diigo.com/", "cost": "100% Free", "action": "Bookmark Link", "how_to_perform": "Save and share annotations and bookmarks on diigo.com with descriptive tags."}
        ],
    },

    "Blog Comments": {
        "icon": "💬",
        "description": "Leave genuine, value-adding comments on high-authority blogs in your niche to build relationships and backlinks.",
        "task_type": "Blog Commenting",
        "platforms": [
            {"name": "Disqus", "domain": "disqus.com", "url": "https://disqus.com/", "cost": "100% Free", "action": "Comment on Blogs", "how_to_perform": "Create a Disqus profile at disqus.com, add your website URL to your profile, then comment on high-DA blogs that use Disqus."},
            {"name": "WordPress.com Blogs", "domain": "wordpress.com", "url": "https://wordpress.com/", "cost": "100% Free", "action": "Leave Comment", "how_to_perform": "Find relevant WordPress.com blogs in your niche, leave genuine, detailed comments with your website URL in the URL field."},
            {"name": "Blogger Blogs", "domain": "blogger.com", "url": "https://www.blogger.com/", "cost": "100% Free", "action": "Leave Comment", "how_to_perform": "Find relevant Blogger/Blogspot blogs, sign in with Google, leave insightful comments with your website URL in your profile."},
            {"name": "Medium Responses", "domain": "medium.com", "url": "https://medium.com/", "cost": "100% Free", "action": "Leave Response", "how_to_perform": "Sign up at medium.com, find relevant articles, leave thoughtful responses with your website link naturally mentioned."},
            {"name": "LinkedIn Comments", "domain": "linkedin.com", "url": "https://www.linkedin.com/", "cost": "100% Free", "action": "Comment on Posts", "how_to_perform": "Log in to LinkedIn, find posts by industry leaders, leave valuable comments that establish expertise and link to relevant content."},
            {"name": "Quora Answers", "domain": "quora.com", "url": "https://www.quora.com/", "cost": "100% Free", "action": "Answer Questions", "how_to_perform": "Register at quora.com, search for questions in your niche, write detailed answers, include your website URL as a reference."},
            {"name": "Reddit Comments", "domain": "reddit.com", "url": "https://www.reddit.com/", "cost": "100% Free", "action": "Reply to Threads", "how_to_perform": "Join Reddit, find relevant subreddits, reply to questions with detailed, helpful answers, include your site URL only when genuinely helpful."},
            {"name": "FastCompany Community", "domain": "fastcompany.com", "url": "https://www.fastcompany.com/", "cost": "100% Free", "action": "Engage & Discuss", "how_to_perform": "Contribute thoughtful comments on business innovation articles on fastcompany.com with your profile URL."},
            {"name": "TechCrunch Discussions", "domain": "techcrunch.com", "url": "https://techcrunch.com/", "cost": "100% Free", "action": "Comment on News", "how_to_perform": "Participate in startup news commentary on techcrunch.com establishing industry authority."},
            {"name": "HubSpot Community", "domain": "hubspot.com", "url": "https://community.hubspot.com/", "cost": "100% Free", "action": "Answer Forum Posts", "how_to_perform": "Help marketing professionals on community.hubspot.com with practical advice linking to your solutions."}
        ],
    },

    "Competitor Backlinks": {
        "icon": "🔗",
        "description": "Submit your RSS feed and blog to directories to replicate competitor backlink sources.",
        "task_type": "RSS & Feed Submission",
        "platforms": [
            {"name": "Feedburner", "domain": "feedburner.google.com", "url": "https://feedburner.google.com/", "cost": "100% Free", "action": "Submit RSS Feed", "how_to_perform": "Go to feedburner.google.com, sign in with Google, enter your blog's RSS feed URL to burn it and get a FeedBurner URL."},
            {"name": "AllTop", "domain": "alltop.com", "url": "https://alltop.com/", "cost": "100% Free", "action": "Submit RSS Feed", "how_to_perform": "Go to alltop.com, submit your RSS feed URL to be listed in your relevant topic category."},
            {"name": "Blogarama", "domain": "blogarama.com", "url": "https://www.blogarama.com/", "cost": "100% Free", "action": "Add Blog", "how_to_perform": "Register at blogarama.com, submit your blog URL and RSS feed URL in the relevant category."},
            {"name": "OnTopList", "domain": "ontoplist.com", "url": "https://www.ontoplist.com/", "cost": "100% Free", "action": "Submit RSS", "how_to_perform": "Go to ontoplist.com, register and submit your RSS feed URL in the appropriate category."},
            {"name": "Feedspot", "domain": "feedspot.com", "url": "https://www.feedspot.com/", "cost": "100% Free", "action": "Submit Feed", "how_to_perform": "Go to feedspot.com, search for your blog, or click 'Add Feed' and enter your RSS URL to get listed."},
            {"name": "Ahrefs Webmaster Tools", "domain": "ahrefs.com", "url": "https://ahrefs.com/webmaster-tools", "cost": "100% Free", "action": "Register Site", "how_to_perform": "Sign up free at ahrefs.com/webmaster-tools, verify your site, and check your competitors' backlinks to find replicable opportunities."},
            {"name": "SEMrush", "domain": "semrush.com", "url": "https://www.semrush.com/", "cost": "100% Free (limited)", "action": "Backlink Gap", "how_to_perform": "Create a free SEMrush account at semrush.com, use the Backlink Gap tool to find sites linking to competitors but not to you."},
            {"name": "SimilarWeb", "domain": "similarweb.com", "url": "https://www.similarweb.com/", "cost": "100% Free (limited)", "action": "Referral Analysis", "how_to_perform": "Analyze competitors' top referring traffic sources and build matching outreach links."},
            {"name": "Moz Link Explorer", "domain": "moz.com", "url": "https://moz.com/link-explorer", "cost": "100% Free (limited)", "action": "Link Research", "how_to_perform": "Inspect competitor inbound links and claim unlinked brand mentions."},
            {"name": "Feedly", "domain": "feedly.com", "url": "https://feedly.com/", "cost": "100% Free", "action": "Submit Blog Feed", "how_to_perform": "Ensure your blog RSS feed is indexed and searchable on Feedly to attract RSS subscribers."}
        ],
    },

    "Google Business Profile": {
        "icon": "📌",
        "description": "Optimise your Google Business Profile and core citations for maximum local search visibility and trust signals.",
        "task_type": "Local SEO & Presence",
        "platforms": [
            {"name": "Google Business Profile", "domain": "business.google.com", "url": "https://business.google.com/", "cost": "100% Free", "action": "Create/Optimise Profile", "how_to_perform": "Visit business.google.com, sign in with Google, claim or create your business listing, fill in ALL fields, and verify."},
            {"name": "Bing Places for Business", "domain": "bingplaces.com", "url": "https://www.bingplaces.com/", "cost": "100% Free", "action": "Claim Bing Listing", "how_to_perform": "Sync directly with Google Business Profile on bingplaces.com for automatic verification."},
            {"name": "Apple Business Connect", "domain": "apple.com", "url": "https://mapsconnect.apple.com/", "cost": "100% Free", "action": "Claim Apple Placecard", "how_to_perform": "Claim and verify your business listing across Apple Maps and Siri search."},
            {"name": "Yelp for Business", "domain": "yelp.com", "url": "https://biz.yelp.com/", "cost": "100% Free", "action": "Manage Yelp Listing", "how_to_perform": "Claim your Yelp business page and maintain up-to-date website links and business hours."},
            {"name": "TripAdvisor", "domain": "tripadvisor.com", "url": "https://www.tripadvisor.com/", "cost": "100% Free", "action": "Claim Listing", "how_to_perform": "Claim your company profile on tripadvisor.com for hospitality, events, or local attraction authority."},
            {"name": "Better Business Bureau", "domain": "bbb.org", "url": "https://www.bbb.org/", "cost": "100% Free", "action": "Create BBB Profile", "how_to_perform": "Create a free business listing on bbb.org to establish foundational trust signals."},
            {"name": "YellowPages", "domain": "yellowpages.com", "url": "https://www.yellowpages.com/", "cost": "100% Free", "action": "Add Free Listing", "how_to_perform": "List your business on the YellowPages national directory with your website URL."},
            {"name": "Chamber of Commerce", "domain": "chamberofcommerce.com", "url": "https://www.chamberofcommerce.com/", "cost": "100% Free", "action": "Register Business", "how_to_perform": "Add your business to the nationwide Chamber of Commerce directory."},
            {"name": "Angi", "domain": "angi.com", "url": "https://www.angi.com/", "cost": "100% Free", "action": "Claim Pro Profile", "how_to_perform": "Claim a business profile on angi.com for home and professional service search presence."}
        ],
    },

    "Quora Links": {
        "icon": "❓",
        "description": "Answer niche questions on authority Q&A platforms to drive referral traffic and earn contextual backlinks.",
        "task_type": "Q&A Participation",
        "platforms": [
            {"name": "Quora", "domain": "quora.com", "url": "https://www.quora.com/", "cost": "100% Free", "action": "Answer Questions", "how_to_perform": "Register at quora.com, search for questions in your niche, write comprehensive answers (300+ words), and include your website URL as a reference source."},
            {"name": "Stack Overflow", "domain": "stackoverflow.com", "url": "https://stackoverflow.com/", "cost": "100% Free", "action": "Answer & Help", "how_to_perform": "Provide technical answers in your area of expertise on stackoverflow.com and link to open-source docs."},
            {"name": "Stack Exchange", "domain": "stackexchange.com", "url": "https://stackexchange.com/", "cost": "100% Free", "action": "Participate in Topic", "how_to_perform": "Join relevant topic communities (e.g. webmasters, software, business) and answer community questions."},
            {"name": "Super User", "domain": "superuser.com", "url": "https://superuser.com/", "cost": "100% Free", "action": "Answer Computer Tech", "how_to_perform": "Contribute solutions to hardware, OS, and productivity software questions."},
            {"name": "Ask.fm", "domain": "ask.fm", "url": "https://ask.fm/", "cost": "100% Free", "action": "Answer Community", "how_to_perform": "Create a brand Q&A desk on ask.fm and answer audience inquiries."},
            {"name": "Answers.com", "domain": "answers.com", "url": "https://www.answers.com/", "cost": "100% Free", "action": "Provide Answers", "how_to_perform": "Answer factual and educational queries on answers.com citing your authoritative guides."},
            {"name": "Spiceworks Community", "domain": "spiceworks.com", "url": "https://community.spiceworks.com/", "cost": "100% Free", "action": "IT Discussions", "how_to_perform": "Participate in IT and software infrastructure discussions with your business profile."},
            {"name": "Digital Point Forums", "domain": "digitalpoint.com", "url": "https://forums.digitalpoint.com/", "cost": "100% Free", "action": "Forum Discussions", "how_to_perform": "Participate in webmaster, marketing, and SEO forum threads with your signature URL."},
            {"name": "Warrior Forum", "domain": "warriorforum.com", "url": "https://www.warriorforum.com/", "cost": "100% Free", "action": "Marketing Discussions", "how_to_perform": "Share actionable digital marketing advice on warriorforum.com with contextual citations."},
            {"name": "SitePoint Community", "domain": "sitepoint.com", "url": "https://www.sitepoint.com/community/", "cost": "100% Free", "action": "Tech Discussions", "how_to_perform": "Discuss web design, development, and hosting on sitepoint.com/community."}
        ],
    },

    "Reddit Communities": {
        "icon": "🟠",
        "description": "Engage in relevant Reddit and forum communities to build brand authority and referral traffic.",
        "task_type": "Community Engagement",
        "platforms": [
            {"name": "Reddit", "domain": "reddit.com", "url": "https://www.reddit.com/", "cost": "100% Free", "action": "Post & Comment", "how_to_perform": "Create a Reddit account, find top subreddits in your niche, contribute genuine value through comments and posts for 2+ weeks before including links to your site."},
            {"name": "Discord", "domain": "discord.com", "url": "https://discord.com/", "cost": "100% Free", "action": "Join Hubs", "how_to_perform": "Participate in public industry Discord servers and share insights and resources."},
            {"name": "Lemmy", "domain": "join-lemmy.org", "url": "https://join-lemmy.org/", "cost": "100% Free", "action": "Post in Fediverse", "how_to_perform": "Share articles and join discussions across federated Lemmy communities."},
            {"name": "Lobsters", "domain": "lobste.rs", "url": "https://lobste.rs/", "cost": "100% Free", "action": "Share Tech Links", "how_to_perform": "Submit high-value technical articles and engage in discussions on lobste.rs."},
            {"name": "Indie Hackers", "domain": "indiehackers.com", "url": "https://www.indiehackers.com/", "cost": "100% Free", "action": "Share Case Study", "how_to_perform": "Post founder milestones, revenue metrics, and growth strategies on indiehackers.com."},
            {"name": "Product Hunt Community", "domain": "producthunt.com", "url": "https://www.producthunt.com/discussions", "cost": "100% Free", "action": "Participate in Discussions", "how_to_perform": "Join daily discussions on product trends, tools, and startup launches on Product Hunt."},
            {"name": "Hacker News", "domain": "news.ycombinator.com", "url": "https://news.ycombinator.com/", "cost": "100% Free", "action": "Comment on Stories", "how_to_perform": "Provide insightful technical commentary on relevant HN threads without aggressive self-promotion."}
        ],
    },

    "Pinterest Submission": {
        "icon": "📌",
        "description": "Create and share Pins on visual bookmarking platforms to drive referral traffic with keyword-rich image content.",
        "task_type": "Social Bookmarking",
        "platforms": [
            {"name": "Pinterest", "domain": "pinterest.com", "url": "https://www.pinterest.com/", "cost": "100% Free", "action": "Create Pins & Boards", "how_to_perform": "Create a business account at pinterest.com, create boards for each topic in your niche, create Pins with your images, write keyword-rich descriptions, and set your website URL as the Pin destination link."},
            {"name": "Pearltrees", "domain": "pearltrees.com", "url": "https://www.pearltrees.com/", "cost": "100% Free", "action": "Curate Visual Web", "how_to_perform": "Organize your web pages and visual assets into public topic trees on pearltrees.com."},
            {"name": "We Heart It", "domain": "weheartit.com", "url": "https://weheartit.com/", "cost": "100% Free", "action": "Heart & Share Images", "how_to_perform": "Upload aesthetic infographics and branded graphics on weheartit.com with site attribution."},
            {"name": "Raindrop.io", "domain": "raindrop.io", "url": "https://raindrop.io/", "cost": "100% Free", "action": "Create Visual Board", "how_to_perform": "Create a public curated visual collection of bookmarks pointing to your best guides."},
            {"name": "Wakelet", "domain": "wakelet.com", "url": "https://wakelet.com/", "cost": "100% Free", "action": "Create Collection", "how_to_perform": "Curate visual stories and link lists on wakelet.com and share them publicly."},
            {"name": "Pocket", "domain": "getpocket.com", "url": "https://getpocket.com/", "cost": "100% Free", "action": "Save & Recommend", "how_to_perform": "Save and recommend your best publications to Pocket's public discovery network."},
            {"name": "Folkd", "domain": "folkd.com", "url": "https://www.folkd.com/", "cost": "100% Free", "action": "Submit Bookmark", "how_to_perform": "Submit URLs with custom tags and descriptions on folkd.com social bookmarking."}
        ],
    },

    "Reblogging": {
        "icon": "🔄",
        "description": "Reshare and reblog content on Web 2.0 platforms to reach new audiences and earn syndication links.",
        "task_type": "Content Syndication",
        "platforms": [
            {"name": "Tumblr Reblog", "domain": "tumblr.com", "url": "https://www.tumblr.com/", "cost": "100% Free", "action": "Reblog Content", "how_to_perform": "Sign in to Tumblr, find relevant content in your niche, click 'Reblog', add your commentary and website URL, then post."},
            {"name": "Medium (Syndication)", "domain": "medium.com", "url": "https://medium.com/", "cost": "100% Free", "action": "Import Story", "how_to_perform": "In Medium, use 'Import a story' from your blog's RSS or URL to republish existing posts with canonical links back to your site."},
            {"name": "Substack Syndication", "domain": "substack.com", "url": "https://substack.com/", "cost": "100% Free", "action": "Republish Newsletter", "how_to_perform": "Republish high-performing articles on Substack with explicit canonical references to your primary domain."},
            {"name": "LinkedIn Pulse", "domain": "linkedin.com", "url": "https://www.linkedin.com/", "cost": "100% Free", "action": "Syndicate Article", "how_to_perform": "Syndicate excerpts of blog posts on LinkedIn Articles with clear calls-to-action to read the full guide on your site."},
            {"name": "Hashnode Cross-post", "domain": "hashnode.com", "url": "https://hashnode.com/", "cost": "100% Free", "action": "Cross-post Article", "how_to_perform": "Use Hashnode's native canonical URL setting when cross-posting tech articles to protect SEO value."},
            {"name": "Dev.to Syndication", "domain": "dev.to", "url": "https://dev.to/", "cost": "100% Free", "action": "Add Canonical Link", "how_to_perform": "In Dev.to article frontmatter, add canonical_url pointing to your blog to earn safe syndication visibility."}
        ],
    },

    "Google Stacking": {
        "icon": "📂",
        "description": "Use Google's own properties (Docs, Sites, Sheets) to create an interlinked entity that boosts your domain authority.",
        "task_type": "Google Entity Stack",
        "platforms": [
            {"name": "Google Sites", "domain": "sites.google.com", "url": "https://sites.google.com/", "cost": "100% Free", "action": "Create Site", "how_to_perform": "Go to sites.google.com, create a new site, build pages about your business/niche, embed Google Docs/Sheets, and link prominently to your main website URL."},
            {"name": "Google Docs", "domain": "docs.google.com", "url": "https://docs.google.com/", "cost": "100% Free", "action": "Create Public Doc", "how_to_perform": "Create a Google Doc with your business info and niche content, make it publicly viewable (Share > Anyone with link), and include links to your website."},
            {"name": "Google Drive", "domain": "drive.google.com", "url": "https://drive.google.com/", "cost": "100% Free", "action": "Create Public Folder", "how_to_perform": "Create a public Google Drive folder, upload branded documents and PDFs that link back to your website, and share the folder link."},
            {"name": "Google Sheets", "domain": "sheets.google.com", "url": "https://sheets.google.com/", "cost": "100% Free", "action": "Create Public Sheet", "how_to_perform": "Create a Google Sheet with useful data for your niche (e.g. resources list), make it public, and include your website URL in cells and notes."},
            {"name": "Google Slides", "domain": "slides.google.com", "url": "https://slides.google.com/", "cost": "100% Free", "action": "Create Presentation", "how_to_perform": "Create a Google Slides presentation about your business/niche, make it public, embed your website URL on each slide as a footer."},
            {"name": "Google Forms", "domain": "forms.google.com", "url": "https://forms.google.com/", "cost": "100% Free", "action": "Create Public Form", "how_to_perform": "Create a Google Form (survey or lead gen), make it public, include your brand name and website URL in the form header/description."},
            {"name": "Google Calendar", "domain": "calendar.google.com", "url": "https://calendar.google.com/", "cost": "100% Free", "action": "Create Public Calendar", "how_to_perform": "Create a Google Calendar for your business events, make it public, add events with your website URL in the event descriptions."},
            {"name": "Blogger (Google)", "domain": "blogger.com", "url": "https://www.blogger.com/", "cost": "100% Free", "action": "Create Blog", "how_to_perform": "Sign in at blogger.com with Google, create a blog about your niche, write posts linking back to your main website."},
            {"name": "Google Drawings", "domain": "drawings.google.com", "url": "https://docs.google.com/drawings/", "cost": "100% Free", "action": "Create Public Diagram", "how_to_perform": "Create business process or flow diagrams on Google Drawings, share publicly, and link to your service pages."},
            {"name": "Google Looker Studio", "domain": "lookerstudio.google.com", "url": "https://lookerstudio.google.com/", "cost": "100% Free", "action": "Publish Dashboard", "how_to_perform": "Publish a public niche data or KPI dashboard on Looker Studio with link attribution to your site."},
            {"name": "Google Colab", "domain": "colab.research.google.com", "url": "https://colab.research.google.com/", "cost": "100% Free", "action": "Share Notebook", "how_to_perform": "Create a helpful public Colab Python tutorial or calculator notebook referencing your tools and domain."}
        ],
    },
}

# --------------------------------------------------------------------------- #
# Presence Checking Metadata
# --------------------------------------------------------------------------- #
LOGIN_WALL_DOMAINS = {
    # Strictly gated social networks / walled accounts
    "linkedin.com", "x.com", "threads.net", "facebook.com", "instagram.com",
    # Google docs/workspace (private by default until user creates & shares)
    "sites.google.com", "docs.google.com", "sheets.google.com", "slides.google.com",
    "drive.google.com", "forms.google.com", "calendar.google.com",
}

PROBE_PATTERNS = {
    # --- Web 2.0 & Blogs (subdomain style) ---
    "wordpress.com":   ["https://{slug}.wordpress.com/"],
    "blogger.com":     ["https://{slug}.blogspot.com/"],
    "tumblr.com":      ["https://{slug}.tumblr.com/"],
    "weebly.com":      ["https://{slug}.weebly.com/"],
    "substack.com":    ["https://{slug}.substack.com/"],
    "livejournal.com": ["https://{slug}.livejournal.com/"],
    "typepad.com":     ["https://{slug}.typepad.com/"],
    "jimdo.com":       ["https://{slug}.jimdofree.com/"],
    "strikingly.com":  ["https://{slug}.mystrikingly.com/"],
    "hashnode.com":    ["https://hashnode.com/@{slug}", "https://hashnode.com/{slug}", "https://{slug}.hashnode.dev/"],
    "yola.com":        ["https://{slug}.yolasite.com/"],
    "over-blog.com":   ["https://{slug}.over-blog.com/"],
    "site123.com":     ["https://{slug}.site123.me/"],
    "carrd.co":        ["https://{slug}.carrd.co/"],
    # --- Profile & Author style ---
    "medium.com":      ["https://medium.com/@{slug}"],
    "hubpages.com":    ["https://hubpages.com/@{slug}"],
    "dev.to":          ["https://dev.to/{slug}"],
    "vocal.media":     ["https://vocal.media/authors/{slug}"],
    "write.as":        ["https://write.as/{slug}/"],
    "github.com":      ["https://github.com/{slug}"],
    "gitlab.com":      ["https://gitlab.com/{slug}"],
    "behance.net":     ["https://www.behance.net/{slug}"],
    "about.me":        ["https://about.me/{slug}"],
    "gravatar.com":    ["https://gravatar.com/{slug}"],
    "dribbble.com":    ["https://dribbble.com/{slug}"],
    "crunchbase.com":  ["https://www.crunchbase.com/organization/{slug}"],
    "producthunt.com": ["https://www.producthunt.com/@{slug}"],
    "wellfound.com":   ["https://wellfound.com/company/{slug}"],
    "clutch.co":       ["https://clutch.co/profile/{slug}"],
    "goodfirms.co":    ["https://www.goodfirms.co/company/{slug}"],
    "linktr.ee":       ["https://linktr.ee/{slug}"],
    "bento.me":        ["https://bento.me/{slug}"],
    "bio.link":        ["https://bio.link/{slug}"],
    "penzu.com":       ["https://penzu.com/p/{slug}"],
    "tealfeed.com":    ["https://tealfeed.com/{slug}"],
    "steemit.com":     ["https://steemit.com/@{slug}"],
    "hive.blog":       ["https://hive.blog/@{slug}"],
    # --- Media, Visual & Presentation ---
    "soundcloud.com":  ["https://soundcloud.com/{slug}"],
    "speakerdeck.com": ["https://speakerdeck.com/{slug}"],
    "slideshare.net":  ["https://www.slideshare.net/{slug}"],
    "scribd.com":      ["https://www.scribd.com/{slug}"],
    "issuu.com":       ["https://issuu.com/{slug}"],
    "vimeo.com":       ["https://vimeo.com/{slug}"],
    "dailymotion.com": ["https://www.dailymotion.com/{slug}"],
    "youtube.com":     ["https://www.youtube.com/@{slug}/about"],
    "flickr.com":      ["https://www.flickr.com/people/{slug}/"],
    "imgur.com":       ["https://imgur.com/user/{slug}"],
    "deviantart.com":  ["https://www.deviantart.com/{slug}"],
    "unsplash.com":    ["https://unsplash.com/@{slug}"],
    "pexels.com":      ["https://www.pexels.com/@{slug}/"],
    "500px.com":       ["https://500px.com/p/{slug}"],
    "pinterest.com":   ["https://www.pinterest.com/{slug}/"],
    "raindrop.io":     ["https://raindrop.io/{slug}"],
    "wakelet.com":     ["https://wakelet.com/@{slug}"],
    "pearltrees.com":  ["https://www.pearltrees.com/{slug}"],
    # --- Microblog & Fediverse ---
    "mastodon.social": ["https://mastodon.social/@{slug}"],
    "bsky.app":        ["https://bsky.app/profile/{slug}.bsky.social"],
    "plurk.com":       ["https://www.plurk.com/{slug}"],
    "scoop.it":        ["https://www.scoop.it/u/{slug}"],
    "flipboard.com":   ["https://flipboard.com/@{slug}"],
    "alternativeto.net": ["https://alternativeto.net/software/{slug}/"],
    # --- Review & Directory (domain keyed) ---
    "trustpilot.com":  ["https://www.trustpilot.com/review/{target}"],
    "sitejabber.com":  ["https://www.sitejabber.com/reviews/{target}"],
    "manta.com":       ["https://www.manta.com/c/{slug}"],
}


def _apply_presence_metadata(platforms: dict) -> None:
    """Adds 'probe' and 'login_wall' to each platform in SUBMISSION_PLATFORMS."""
    for cat in platforms.values():
        for p in cat.get("platforms", []):
            dom = p.get("domain", "")
            if "probe" not in p:
                p["probe"] = list(PROBE_PATTERNS.get(dom, []))
            if "login_wall" not in p:
                p["login_wall"] = dom in LOGIN_WALL_DOMAINS and not p["probe"]


_apply_presence_metadata(SUBMISSION_PLATFORMS)

