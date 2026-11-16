var app = angular.module("farmingApp", []);


app.config(function($interpolateProvider) {

    $interpolateProvider.startSymbol("[[");
    $interpolateProvider.endSymbol("]]");

});


app.controller("DashboardController", function($scope) {


    $scope.currentLanguage = "en";


    $scope.text = {


        // =========================
        // ENGLISH
        // =========================

        en: {

            welcome:
            "Welcome to AI Smart Farming Assistant",

            subtitle:
            "Smart Solutions for Better Farming with Artificial Intelligence",


            dashboard: "Dashboard",

            profile: "Profile",

            history: "History",

            about: "About Us",

            contact: "Contact Us",

            logout: "Logout",


            disease:
            "Disease Detection",

            diseaseDesc:
            "Upload crop leaf image and detect possible diseases using AI.",

            detectDisease:
            "Detect Disease",


            chatbot:
            "AI Agriculture Chatbot",

            chatbotDesc:
            "Ask your farming questions and get AI-based answers.",

            askChatbot:
            "Ask Chatbot",


            weather:
            "Weather Information",

            weatherDesc:
            "Get current weather updates including temperature, rainfall and humidity.",

            checkWeather:
            "Check Weather",


            irrigation:
            "Irrigation Advice",

            irrigationDesc:
            "Get smart suggestions about when and how much to water your crop.",

            irrigationButton:
            "Get Advice",


            fertilizer: 
             "Fertilizer Recommendation",

            fertilizerDesc: 
              "Get fertilizer suggestions according to crop and growth stage.",

            fertilizerButton: 
             "Get Recommendation",

            market:
            "Market Prices",

            marketDesc:
            "Check current market prices of crops from nearby markets.",

            viewPrices:
            "View Prices",


            crop:
            "Crop",

            soil:
            "Soil",

            irrigationStatus:
            "Irrigation",

            weatherStatus:
            "Weather",


            contactTitle:
            "Contact Us",

            contactSubtitle:
            "Contact us for farming assistance.",

            phone:
            "Phone",


            footer:
            "© 2026 AI Smart Farming Assistant | Smart Technology for Better Farming"

        },


        // =========================
        // MARATHI
        // =========================

        mr: {

            welcome:
            "AI स्मार्ट फार्मिंग असिस्टंटमध्ये स्वागत आहे",

            subtitle:
            "कृत्रिम बुद्धिमत्तेच्या मदतीने शेतीसाठी स्मार्ट उपाय",


            dashboard:
            "डॅशबोर्ड",

            profile:
            "प्रोफाइल",

            history:
            "इतिहास",

            about:
            "आमच्याबद्दल",

            contact:
            "संपर्क करा",

            logout:
            "लॉगआउट",


            disease:
            "पिकांचे रोग ओळख",

            diseaseDesc:
            "पिकाच्या पानाचा फोटो अपलोड करून AI च्या मदतीने रोग ओळखा.",

            detectDisease:
            "रोग ओळखा",


            chatbot:
            "AI कृषी चॅटबॉट",

            chatbotDesc:
            "तुमचे शेतीविषयक प्रश्न विचारा आणि AI कडून उत्तरे मिळवा.",

            askChatbot:
            "चॅटबॉटला विचारा",


            weather:
            "हवामान माहिती",

            weatherDesc:
            "तापमान, पाऊस आणि आर्द्रतेसह सध्याची हवामान माहिती मिळवा.",

            checkWeather:
            "हवामान तपासा",


            irrigation:
            "सिंचन सल्ला",

            irrigationDesc:
            "पिकाला कधी आणि किती पाणी द्यावे याबद्दल स्मार्ट सल्ला मिळवा.",

            irrigationButton:
            "सल्ला मिळवा",


            fertilizer: 
             "खत शिफारस",

            fertilizerDesc: 
             "पीक आणि वाढीच्या अवस्थेनुसार योग्य खताची शिफारस मिळवा.",

            fertilizerButton: 
             "शिफारस मिळवा",


            market:
            "बाजार भाव",

            marketDesc:
            "जवळच्या बाजारातील पिकांचे सध्याचे बाजार भाव तपासा.",

            viewPrices:
            "बाजार भाव पहा",


            crop:
            "पीक",

            soil:
            "जमीन",

            irrigationStatus:
            "सिंचन",

            weatherStatus:
            "हवामान",


            contactTitle:
            "संपर्क करा",

            contactSubtitle:
            "शेतीसाठी मदतीसाठी आमच्याशी संपर्क साधा.",

            phone:
            "फोन",


            footer:
            "© 2026 AI स्मार्ट फार्मिंग असिस्टंट | चांगल्या शेतीसाठी स्मार्ट तंत्रज्ञान"

        }

    };


    // =========================
    // LANGUAGE CHANGE
    // =========================

    $scope.changeLanguage = function(language) {

        $scope.currentLanguage = language;

    };

});