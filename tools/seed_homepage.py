from apps.core.models import HomePage

# 1. Conversation Flow Data
phone_chat_data = [
    {
        "role": "user",
        "type": "text",
        "content": "Price of the Premium Silk Panjabi?",
        "cooldown": 1800
    },
    {
        "role": "bot",
        "type": "text",
        "content": "Hi there! Our Premium Crimson Silk Panjabi is crafted from 100% pure organic silk, featuring elegant hand-embroidery on the collar and a modern slim-fit cut. Here is our exclusive festive collection:",
        "cooldown": 600
    },
    {
        "role": "bot",
        "type": "products",
        "content": [
            {
                "title": "Crimson Silk Panjabi",
                "subtitle": "৳3,450 Sizes: M, L, XL, XXL. Premium organic silk.",
                "image": "data:image/jpeg;base64,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"
            },
            {
                "title": "Royal Blue Silk Panjabi",
                "subtitle": "৳3,450 Sizes: M, L, XL. Elegant hand embroideries.",
                "image": "data:image/jpeg;base64,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"
            }
        ],
        "cooldown": 2500
    },
    {
        "role": "user",
        "type": "text",
        "content": "I want to buy a Crimson Silk Panjabi.",
        "cooldown": 1000
    },
    {
        "role": "bot",
        "type": "text",
        "content": "Perfect! Please reply with your Full Name, Phone Number, and Complete Delivery Address to secure your package.",
        "cooldown": 1500
    },
    {
        "role": "user",
        "type": "text",
        "content": "Farhan Islam, 01712345678, Flat 4A, Road 12, Banani, Dhaka",
        "cooldown": 1200
    },
    {
        "role": "bot",
        "type": "text",
        "content": "Thank you, Farhan! Processing your order right now...",
        "cooldown": 1000
    },
    {
        "role": "bot",
        "type": "receipt",
        "content": "ORDER CONFIRMED\nOrder ID: #BKR-89210\nCustomer: Farhan Islam\nProduct: Crimson Silk Panjabi (L)\nTotal Price: ৳3,450\nDelivery Method: Cash on Delivery\nEst. Arrival: 1-2 Days",
        "cooldown": 1000
    },
    {
        "role": "bot",
        "type": "text",
        "content": "Your order is successfully confirmed! We've sent a WhatsApp notification with your invoice and delivery tracking link. Thank you for shopping with us!",
        "cooldown": 5000
    }
]

# 2. Brands Data
brands_data = [
    {
        "name": "10 Minute School",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/10_Minute_School_Logo.svg/960px-10_Minute_School_Logo.svg.png?utm_source=commons.wikimedia.org&utm_campaign=index&utm_content=thumbnail&_=20220226144707",
        "url": "https://10minuteschool.com/"
    },
    {
        "name": "Nagad",
        "logo": "https://upload.wikimedia.org/wikipedia/bn/thumb/9/97/%E0%A6%A8%E0%A6%97%E0%A6%A6%E0%A7%87%E0%A6%B0_%E0%A6%B2%E0%A7%8B%E0%A6%97%E0%A7%8B.svg/250px-%E0%A6%A8%E0%A6%97%E0%A6%A6%E0%A7%87%E0%A6%B0_%E0%A6%B2%E0%A7%8B%E0%A6%97%E0%A7%8B.svg.png",
        "url": "https://www.nagad.com.bd"
    },
    {
        "name": "Pathao",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/2/26/Pathao_-_Here_with_You.png",
        "url": "https://pathao.com"
    },
    {
        "name": "Daraz",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Daraz_Logo.png/960px-Daraz_Logo.png",
        "url": "https://www.daraz.com.bd"
    },
    {
        "name": "Walton",
        "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/3/3b/Walton_Group.svg/960px-Walton_Group.svg.png",
        "url": "https://www.walton.com"
    },
    {
        "name": "Robi",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Robi_Axiata_logo.svg/120px-Robi_Axiata_logo.svg.png",
        "url": "https://www.robi.com"
    }
]

# 4. Reviews Data
reviews_data = [
    {
        "name": "তাসনিম চৌধুরী",
        "designation": "প্রতিষ্ঠাতা, জারার উৎসব বুটিক",
        "photo": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=100&h=100&q=80",
        "rating": 5.0,
        "comment": "বিক্রিএআই-এর আগে আমি প্রতিদিন ৬ ঘণ্টা ধরে 'দাম বলুন' মন্তব্যের জবাব দিতাম। এখন এআই ৯০% মৌলিক সাইজ এবং দামের প্রশ্নের উত্তর দেয়, অর্ডার সংগ্রহ করে এবং বিবরণ সংরক্ষণ করে। গ্রাহকরা তাৎক্ষণিক জবাব পাওয়ার কারণে মাত্র এক মাসে আমার বিক্রয় ৪২% বৃদ্ধি পেয়েছে!"
    },
    {
        "name": "ইমতিয়াজ আহমেদ",
        "designation": "সহ-প্রতিষ্ঠাতা, ড্রপগিয়ার বাংলাদেশ",
        "photo": "https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&w=100&h=100&q=80",
        "rating": 5.0,
        "comment": "হোয়াটসঅ্যাপ সংযোগ করা অত্যন্ত সহজ ছিল। ক্যাটালগ ক্যারোসেল ডিসপ্লে একটি গেম চেঞ্জার। গ্রাহকরা স্মার্টওয়াচ দেখেন, বৈশিষ্ট্য যাচাই করেন এবং তাৎক্ষণিকভাবে অর্ডার করেন। স্বয়ংক্রিয় ইনভয়েস জেনারেটর অসাধারণ—আর হাতে হাতে গ্রাহক স্লিপ লেখার প্রয়োজন নেই!"
    },
    {
        "name": "মুনতাসির রহমান",
        "designation": "অপারেশন্স ম্যানেজার, বিডি হেরিটেজ আর্ট",
        "photo": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?auto=format&fit=crop&w=100&h=100&q=80",
        "rating": 5.0,
        "comment": "অটো-পজ ফিচারটি জীবন রক্ষাকারী। আমার কর্মীরা কাস্টমাইজড প্রশ্নের উত্তর দেওয়ার মুহূর্তে এআই নির্বিঘ্নে পিছিয়ে যায়। এটি আমাদের দুটি বিশ্বের সেরাটি দেয়: বিদ্যুৎ দ্রুত এআই প্রতিক্রিয়া এবং ব্যক্তিগতকৃত মানব পরামর্শ।"
    }
]

# 5. FAQs Data
faqs_data = [
    {
        "question": "আমি চলবে এআইকে আমার ফেসবুক পেজ এবং হোয়াটসঅ্যাপের সাথে কীভাবে সংযুক্ত করতে পারি?",
        "answer": "এটি একটি নিরাপদ, এক-ক্লিক ইন্টিগ্রেশন। সহজেই চলবে এআই ড্যাশবোর্ডে লগইন করুন, 'প্ল্যাটফর্ম সংযুক্ত করুন' ক্লিক করুন, আপনার ফেসবুক শংসাপত্র দিয়ে লগইন করুন এবং স্বয়ংক্রিয় করতে চান এমন পৃষ্ঠা বা হোয়াটসঅ্যাপ ব্যবসায়িক অ্যাকাউন্টগুলি অনুমোদন করুন। কোনো ডেভেলপার অ্যাকাউন্ট বা কোডিং দক্ষতার প্রয়োজন নেই!"
    },
    {
        "question": "এআই আমার পণ্য এবং স্টোর নীতি সম্পর্কে কীভাবে জানে?",
        "answer": "আপনি একটি সাধারণ সিএসভি টেমপ্লেট ব্যবহার করে আপনার পণ্য আমদানি করতে পারেন, প্যানেল থেকে সরাসরি স্বতন্ত্র আইটেমগুলি কনফিগার করতে পারেন এবং কাস্টম প্রশ্নোত্তর, রিটার্ন নীতি এবং ব্র্যান্ড নির্দেশিকা সহ আপনার 'ব্যবসায়িক প্রোফাইল তথ্য' পূরণ করতে পারেন। এআই তাৎক্ষণিকভাবে এই ডেটা পর্যালোচনা করে এবং শুধুমাত্র আপনি প্রদান করা বিবরণের উপর ভিত্তি করে প্রশ্নের উত্তর দেবে।"
    },
    {
        "question": "যদি কোনো গ্রাহক অত্যন্ত কাস্টম প্রশ্ন জিজ্ঞাসা করে তখন কী ঘটে?",
        "answer": "যখনই কোনো গ্রাহক কিছু জটিল জিজ্ঞাসা করে (যেমন কাস্টম ডিজাইন অনুরোধ বা ডেলিভারি অভিযোগ), আপনার মানব কর্মীরা মেটা ইনবক্স বা হোয়াটসঅ্যাপ ওয়েব থেকে সরাসরি উত্তর দিতে পারেন। এআই এই ম্যানুয়াল মিথস্ক্রিয়া সনাক্ত করে এবং স্বয়ংক্রিয়ভাবে ১৫ মিনিটের জন্য থেমে থাকে, সম্পূর্ণ নিয়ন্ত্রণ মানব এজেন্টকে হাতে তুলে দেয়।"
    },
    {
        "question": "সিস্টেম পরীক্ষা করার জন্য কি বিনামূল্যে ট্রায়াল আছে?",
        "answer": "হ্যাঁ! প্রতিটি নতুন সাইন-আপ ১০ টি বিনামূল্যে কথোপকথন ক্রেডিট পায়। আপনি সম্পূর্ণভাবে আপনার ব্যবসায়িক কনফিগারেশন পরীক্ষা করতে পারেন, দেখতে পারেন এআই আপনার পরীক্ষামূলক বার্তাগুলিতে কীভাবে প্রতিক্রিয়া জানায় এবং অটো-ক্যাপচার অর্ডার ড্যাশবোর্ড অন্বেষণ করতে পারেন এবং তারপর একটি ক্রেডিট সাবস্ক্রিপশন প্যাকেজ বেছে নিতে পারেন।"
    }
]

# 6. Social Links Data
social_links_data = [
    {
        "platform": "Facebook",
        "icon": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><!--!Font Awesome Free v7.2.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2026 Fonticons, Inc.--><path d="M576 320C576 178.6 461.4 64 320 64C178.6 64 64 178.6 64 320C64 440 146.7 540.8 258.2 568.5L258.2 398.2L205.4 398.2L205.4 320L258.2 320L258.2 286.3C258.2 199.2 297.6 158.8 383.2 158.8C399.4 158.8 427.4 162 438.9 165.2L438.9 236C432.9 235.4 422.4 235 409.3 235C367.3 235 351.1 250.9 351.1 292.2L351.1 320L434.7 320L420.3 398.2L351 398.2L351 574.1C477.8 558.8 576 450.9 576 320z"/></svg>',
        "url": "https://facebook.com"
    },
    {
        "platform": "YouTube",
        "icon": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><!--!Font Awesome Free v7.2.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2026 Fonticons, Inc.--><path d="M581.7 188.1C575.5 164.4 556.9 145.8 533.4 139.5C490.9 128 320.1 128 320.1 128C320.1 128 149.3 128 106.7 139.5C83.2 145.8 64.7 164.4 58.4 188.1C47 231 47 320.4 47 320.4C47 320.4 47 409.8 58.4 452.7C64.7 476.3 83.2 494.2 106.7 500.5C149.3 512 320.1 512 320.1 512C320.1 512 490.9 512 533.5 500.5C557 494.2 575.5 476.3 581.8 452.7C593.2 409.8 593.2 320.4 593.2 320.4C593.2 320.4 593.2 231 581.8 188.1zM264.2 401.6L264.2 239.2L406.9 320.4L264.2 401.6z"/></svg>',
        "url": "https://youtube.com"
    },
    {
        "platform": "Instagram",
        "icon": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><!--!Font Awesome Free v7.2.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2026 Fonticons, Inc.--><path d="M320.3 205C256.8 204.8 205.2 256.2 205 319.7C204.8 383.2 256.2 434.8 319.7 435C383.2 435.2 434.8 383.8 435 320.3C435.2 256.8 383.8 205.2 320.3 205zM319.7 245.4C360.9 245.2 394.4 278.5 394.6 319.7C394.8 360.9 361.5 394.4 320.3 394.6C279.1 394.8 245.6 361.5 245.4 320.3C245.2 279.1 278.5 245.6 319.7 245.4zM413.1 200.3C413.1 185.5 425.1 173.5 439.9 173.5C454.7 173.5 466.7 185.5 466.7 200.3C466.7 215.1 454.7 227.1 439.9 227.1C425.1 227.1 413.1 215.1 413.1 200.3zM542.8 227.5C541.1 191.6 532.9 159.8 506.6 133.6C480.4 107.4 448.6 99.2 412.7 97.4C375.7 95.3 264.8 95.3 227.8 97.4C192 99.1 160.2 107.3 133.9 133.5C107.6 159.7 99.5 191.5 97.7 227.4C95.6 264.4 95.6 375.3 97.7 412.3C99.4 448.2 107.6 480 133.9 506.2C160.2 532.4 191.9 540.6 227.8 542.4C264.8 544.5 375.7 544.5 412.7 542.4C448.6 540.7 480.4 532.5 506.6 506.2C532.8 480 541 448.2 542.8 412.3C544.9 375.3 544.9 264.5 542.8 227.5zM495 452C487.2 471.6 472.1 486.7 452.4 494.6C422.9 506.3 352.9 503.6 320.3 503.6C287.7 503.6 217.6 506.2 188.2 494.6C168.6 486.8 153.5 471.7 145.6 452C133.9 422.5 136.6 352.5 136.6 319.9C136.6 287.3 134 217.2 145.6 187.8C153.4 168.2 168.5 153.1 188.2 145.2C217.7 133.5 287.7 136.2 320.3 136.2C352.9 136.2 423 133.6 452.4 145.2C472 153 487.1 168.1 495 187.8C506.7 217.3 504 287.3 504 319.9C504 352.5 506.7 422.6 495 452z"/></svg>',
        "url": "https://instagram.com"
    },
    {
        "platform": "Whatsapp",
        "icon": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><!--!Font Awesome Free v7.2.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2026 Fonticons, Inc.--><path d="M476.9 161.1C435 119.1 379.2 96 319.9 96C197.5 96 97.9 195.6 97.9 318C97.9 357.1 108.1 395.3 127.5 429L96 544L213.7 513.1C246.1 530.8 282.6 540.1 319.8 540.1L319.9 540.1C442.2 540.1 544 440.5 544 318.1C544 258.8 518.8 203.1 476.9 161.1zM319.9 502.7C286.7 502.7 254.2 493.8 225.9 477L219.2 473L149.4 491.3L168 423.2L163.6 416.2C145.1 386.8 135.4 352.9 135.4 318C135.4 216.3 218.2 133.5 320 133.5C369.3 133.5 415.6 152.7 450.4 187.6C485.2 222.5 506.6 268.8 506.5 318.1C506.5 419.9 421.6 502.7 319.9 502.7zM421.1 364.5C415.6 361.7 388.3 348.3 383.2 346.5C378.1 344.6 374.4 343.7 370.7 349.3C367 354.9 356.4 367.3 353.1 371.1C349.9 374.8 346.6 375.3 341.1 372.5C308.5 356.2 287.1 343.4 265.6 306.5C259.9 296.7 271.3 297.4 281.9 276.2C283.7 272.5 282.8 269.3 281.4 266.5C280 263.7 268.9 236.4 264.3 225.3C259.8 214.5 255.2 216 251.8 215.8C248.6 215.6 244.9 215.6 241.2 215.6C237.5 215.6 231.5 217 226.4 222.5C221.3 228.1 207 241.5 207 268.8C207 296.1 226.9 322.5 229.6 326.2C232.4 329.9 268.7 385.9 324.4 410C359.6 425.2 373.4 426.5 391 423.9C401.7 422.3 423.8 410.5 428.4 397.5C433 384.5 433 373.4 431.6 371.1C430.3 368.6 426.6 367.2 421.1 364.5z"/></svg>',
        "url": "https://whatsapp.com"
    },
]

# 7. Link Groups Data
link_groups_data = [
    {
        "group_name": "Products",
        "links": [
            {"name": "Facebook Automation", "url": "/#features"},
            {"name": "WhatsApp Commerce", "url": "/#features"},
            {"name": "AI Catalog Search", "url": "/#features"}
        ]
    },
    {
        "group_name": "Company",
        "links": [
            {"name": "About Us", "url": "/i/about/"},
            {"name": "Contact us", "url": "/i/contact/"},
            {"name": "Pricing", "url": "/#pricing"}
        ]
    },
    {
        "group_name": "Legal Policies",
        "links": [
            {"name": "Privacy Policy", "url": "/i/privacy-policy/"},
            {"name": "Terms of Service", "url": "/i/terms-of-service/"},
            {"name": "Refund Policy", "url": "/i/refund-policy/"}
        ]
    }
]


# Update the database
homepage_instance, created = HomePage.objects.get_or_create(pk=1)
homepage_instance.title = "চলবে এআই  - এআই এজেন্টের মাধ্যমে ফেসবুক ও হোয়াটসঅ্যাপে বিক্রি বাড়ান স্বয়ংক্রিয়ভাবে"
homepage_instance.meta_description = "মেসেঞ্জার ও হোয়াটসঅ্যাপে আপনার ই-কমার্স বা ফেসবুক বিজনেস পরিচালনা করুন সম্পূর্ণ স্বয়ংক্রিয়ভাবে। আমাদের বুদ্ধিমান এআই এজেন্ট ২৪/৭ কাস্টমারদের দাম জানাবে, ক্যাটালগ দেখাবে, ডেলিভারির ঠিকানা নেবে এবং ইনভয়েস তৈরি করবে।"
homepage_instance.meta_keywords = "সোশ্যাল কমার্স অটোমেশন, ফেসবুক মেসেঞ্জার বট, হোয়াটসঅ্যাপ কমার্স বাংলাদেশ, স্বয়ংক্রিয় অর্ডার, এআই কাস্টমার সার্ভিস, এফ-কমার্স অটোমেশন, চলবে এআই "
homepage_instance.hero_tag = "নতুন ফিচার - কমেন্টের অটো আরপ্লাই"
homepage_instance.hero_title = 'বাতি কর্মী ছাড়াই প্রতিটি "দাম কত" কমেন্টকে রূপান্তর করুন <span class="text-primary-500">কনফার্মড অর্ডারে</span>, সম্পূর্ণ স্বয়ংক্রিয়ভাবে।'
homepage_instance.hero_subtitle = "মাত্র এক ক্লিকে যুক্ত করুন আপনার ফেসবুক পেজ এবং হোয়াটসঅ্যাপ বিজনেস নম্বর। আমাদের এআই এজেন্টকে শুধু পণ্যের বিবরণ দিন; বাকি কাজ ও নিজেই করবে! বাংলা ও ইংরেজি—উভয় ভাষায় কাস্টমারের সাথে কথা বলে ডেলিভারির ঠিকানা নেওয়া থেকে শুরু করে ২৪/৭ অর্ডার কনফার্ম করবে মুহূর্তেই।"
homepage_instance.see_demo_url = "#demo"
homepage_instance.phone_chat = phone_chat_data

homepage_instance.pricing_title = "ব্যবসা বাড়ান সাশ্রয়ী খরচে, কোনো গোপন ফি ছাড়াই"
homepage_instance.pricing_subtitle = "আপনার ব্যবসার প্রয়োজন অনুযায়ী বেছে নিন সেরা প্ল্যান। কোনো দীর্ঘমেয়াদী চুক্তি নেই, যখন খুশি আপগ্রেড বা ক্যানসেল করুন।"

homepage_instance.brands_title = "বাংলাদেশের আগামী দিনের সফল ব্র্যান্ডগুলোর ভরসা"
homepage_instance.brands_subtitle = "দেশের দ্রুত বর্ধনশীল সোশ্যাল কমার্স স্টোর, বুটিক হাউস এবং ডিটিসি (D2C) ব্র্যান্ডগুলোর স্বয়ংক্রিয় চেকআউট পার্টনার।"
homepage_instance.brands = brands_data

homepage_instance.reviews_title = "হাজারো সোশ্যাল মার্চেন্ট বা অনলাইন বিক্রেতার নির্ভরযোগ্য সঙ্গী"
homepage_instance.reviews_subtitle = "দেখুন কীভাবে দেশের বুটিক মালিক, ড্রপ-শিপার এবং লোকাল ব্র্যান্ডগুলো 'চলবে এআই ' ব্যবহার করে কোনো ঝামেলা ছাড়াই তাদের ব্যবসার বিক্রি বাড়িয়ে নিচ্ছেন।"
homepage_instance.reviews = reviews_data

homepage_instance.faq_title = "সচরাচর জিজ্ঞাসিত প্রশ্নাবলী (FAQ)"
homepage_instance.faqs = faqs_data

homepage_instance.footer_text = "চলবে এআই  (Cholbe AI) হলো বাংলাদেশের এক নম্বর কনভার্সেশনাল এআই প্ল্যাটফর্ম। যা সোশ্যাল কমার্স উদ্যোক্তাদের ফেসবুক মেসেঞ্জার এবং হোয়াটসঅ্যাপে ২৪/৭ স্বয়ংক্রিয় কাস্টমার সার্ভিস, ক্যাটালগ প্রদর্শন এবং অর্ডার কনফার্ম করতে সাহায্য করে।"
homepage_instance.social_links = social_links_data
homepage_instance.link_groups = link_groups_data

homepage_instance.save()

print("HomePage copywriting database seed applied successfully! (pk=1)")


