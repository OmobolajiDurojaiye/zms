"use strict";

document.addEventListener("DOMContentLoaded", function () {
  const authPage = document.querySelector(".auth-content-card");

  if (authPage) {
    const mainTabButtons = authPage.querySelectorAll(
      ".auth-modal-header .tab-button"
    );
    const mainTabContents = authPage.querySelectorAll(".tab-content");

    function switchTab(tabId, tabButtons, tabContents) {
      tabButtons.forEach((btn) => btn.classList.remove("active"));
      tabContents.forEach((content) => content.classList.remove("active"));

      const buttonToActivate = Array.from(tabButtons).find(
        (btn) => btn.dataset.tab === tabId
      );
      if (buttonToActivate) buttonToActivate.classList.add("active");

      const contentToActivate = document.getElementById(tabId);
      if (contentToActivate) contentToActivate.classList.add("active");
    }

    function switchForm(formId, formToggleButtons, forms) {
      formToggleButtons.forEach((btn) => btn.classList.remove("active"));
      forms.forEach((form) => form.classList.remove("active"));

      const buttonToActivate = Array.from(formToggleButtons).find(
        (btn) => btn.dataset.form === formId
      );
      if (buttonToActivate) buttonToActivate.classList.add("active");

      let formToActivate = document.getElementById(formId);
      if (!formToActivate) {
        const potentialFormId = formId.endsWith("Form")
          ? formId
          : formId + "Form";
        formToActivate = document.getElementById(potentialFormId);
      }

      if (formToActivate) {
        formToActivate.classList.add("active");
      } else {
        const specificForm = Array.from(forms).find((f) =>
          f.id.toLowerCase().startsWith(formId.toLowerCase())
        );
        if (specificForm) specificForm.classList.add("active");
      }
    }

    mainTabButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const tabId = button.dataset.tab;
        switchTab(tabId, mainTabButtons, mainTabContents);
        const activeTabContent = document.getElementById(tabId);
        if (activeTabContent) {
          const formToggleButtons = activeTabContent.querySelectorAll(
            ".form-toggle-button"
          );
          const forms = activeTabContent.querySelectorAll(".auth-form");
          if (formToggleButtons.length > 0 && forms.length > 0) {
            // Default to the first form toggle button in the new tab
            const firstFormToggleButton = formToggleButtons[0];
            if (firstFormToggleButton) {
              switchForm(
                firstFormToggleButton.dataset.form,
                formToggleButtons,
                forms
              );
            }
          }
        }
      });
    });

    mainTabContents.forEach((tabContent) => {
      const formToggleButtons = tabContent.querySelectorAll(
        ".form-toggle-button"
      );
      const forms = tabContent.querySelectorAll(".auth-form");
      formToggleButtons.forEach((button) => {
        button.addEventListener("click", () => {
          switchForm(button.dataset.form, formToggleButtons, forms);
        });
      });
    });

    const params = new URLSearchParams(window.location.search);
    const requestedTab = params.get("tab");
    const requestedFormType = params.get("form"); // "login" or "signup"

    if (requestedTab) {
      const targetMainTabButton = Array.from(mainTabButtons).find(
        (btn) => btn.dataset.tab === requestedTab
      );
      if (targetMainTabButton) {
        switchTab(requestedTab, mainTabButtons, mainTabContents); // Activate the tab first

        const activeTabContent = document.getElementById(requestedTab);
        if (activeTabContent) {
          const formToggleButtons = activeTabContent.querySelectorAll(
            ".form-toggle-button"
          );
          const forms = activeTabContent.querySelectorAll(".auth-form");

          if (requestedFormType) {
            let targetFormDataAttr;
            // Construct the data-form attribute based on tab and form type
            if (requestedTab === "businessOwnerTab") {
              targetFormDataAttr =
                "bo" +
                (requestedFormType.charAt(0).toUpperCase() +
                  requestedFormType.slice(1));
            } else if (requestedTab === "clientTab") {
              targetFormDataAttr =
                "client" +
                (requestedFormType.charAt(0).toUpperCase() +
                  requestedFormType.slice(1));
            }

            const targetFormToggleButton = Array.from(formToggleButtons).find(
              (btn) => btn.dataset.form === targetFormDataAttr
            );

            if (targetFormToggleButton) {
              switchForm(targetFormDataAttr, formToggleButtons, forms);
            } else if (formToggleButtons.length > 0) {
              // Fallback to first form if specific one not found
              switchForm(
                formToggleButtons[0].dataset.form,
                formToggleButtons,
                forms
              );
            }
          } else if (formToggleButtons.length > 0) {
            // If no specific form, default to the first form toggle button in the active tab
            switchForm(
              formToggleButtons[0].dataset.form,
              formToggleButtons,
              forms
            );
          }
        }
      }
    } else if (mainTabButtons.length > 0) {
      // Default behavior: activate first tab and its first form
      const defaultTabId = mainTabButtons[0].dataset.tab;
      switchTab(defaultTabId, mainTabButtons, mainTabContents);
      const defaultTabContent = document.getElementById(defaultTabId);
      if (defaultTabContent) {
        const formToggleButtons = defaultTabContent.querySelectorAll(
          ".form-toggle-button"
        );
        const forms = defaultTabContent.querySelectorAll(".auth-form");
        if (formToggleButtons.length > 0) {
          switchForm(
            formToggleButtons[0].dataset.form,
            formToggleButtons,
            forms
          );
        }
      }
    }
  }

  // --- Dynamic Location Data ---
  const locationData = {
    Nigeria: {
      Abia: [
        "Aba North",
        "Aba South",
        "Isiala Ngwa North",
        "Ukwa West",
        "Ukwa East",
        "Obingwa",
        "Ikwuano",
        "Bende",
        "Arochukwu",
        "Ohafia",
        "Isiala Ngwa South",
        "Umuahia North",
        "Umuahia South",
        "Ugwunagbo",
        "Osisioma",
        "Nnochi",
        "Umunneochi",
      ],
      Adamawa: [
        "Demsa",
        "Fufore",
        "Ganye",
        "Girei",
        "Gombi",
        "Guyuk",
        "Hong",
        "Jada",
        "Lamurde",
        "Madagali",
        "Maiha",
        "Mayo-Belwa",
        "Michika",
        "Mubi North",
        "Mubi South",
        "Numan",
        "Shelleng",
        "Song",
        "Toungo",
        "Yola North",
        "Yola South",
      ],
      "Akwa Ibom": [
        "Abak",
        "Eastern Obolo",
        "Eket",
        "Esit Eket",
        "Essien Udim",
        "Etim Ekpo",
        "Etinan",
        "Ibeno",
        "Ibesikpo Asutan",
        "Ibiono Ibom",
        "Ika",
        "Ikono",
        "Ikot Abasi",
        "Ikot Ekpene",
        "Ini",
        "Itu",
        "Mbo",
        "Mkpat Enin",
        "Nsit Atai",
        "Nsit Ibom",
        "Nsit Ubium",
        "Obot Akara",
        "Okobo",
        "Onna",
        "Oron",
        "Oruk Anam",
        "Udung Uko",
        "Ukanafun",
        "Uruan",
        "Urue-Offong/Oruko",
        "Uyo",
      ],
      Anambra: [
        "Aguata",
        "Anambra East",
        "Anambra West",
        "Anaocha",
        "Awka North",
        "Awka South",
        "Ayamelum",
        "Dunukofia",
        "Ekwusigo",
        "Idemili North",
        "Idemili South",
        "Ihiala",
        "Njikoka",
        "Nnewi North",
        "Nnewi South",
        "Ogbaru",
        "Onitsha North",
        "Onitsha South",
        "Orumba North",
        "Orumba South",
        "Oyi",
      ],
      Bauchi: [
        "Alkaleri",
        "Bauchi",
        "Bogoro",
        "Damban",
        "Darazo",
        "Dass",
        "Gamawa",
        "Ganjuwa",
        "Giade",
        "Itas/Gadau",
        "Jama'are",
        "Katagum",
        "Kirfi",
        "Misau",
        "Ningi",
        "Shira",
        "Tafawa Balewa",
        "Toro",
        "Warji",
        "Zaki",
      ],
      Bayelsa: [
        "Brass",
        "Ekeremor",
        "Kolokuma/Opokuma",
        "Nembe",
        "Ogbia",
        "Sagbama",
        "Southern Ijaw",
        "Yenagoa",
      ],
      Benue: [
        "Ado",
        "Agatu",
        "Apa",
        "Buruku",
        "Gboko",
        "Guma",
        "Gwer East",
        "Gwer West",
        "Katsina-Ala",
        "Konshisha",
        "Kwande",
        "Logo",
        "Makurdi",
        "Obi",
        "Ogbadibo",
        "Ohimini",
        "Oju",
        "Okpokwu",
        "Otukpo",
        "Tarka",
        "Ukum",
        "Ushongo",
        "Vandeikya",
      ],
      Borno: [
        "Abadam",
        "Askira/Uba",
        "Bama",
        "Bayo",
        "Biu",
        "Chibok",
        "Damboa",
        "Dikwa",
        "Gubio",
        "Guzamala",
        "Gwoza",
        "Hawul",
        "Jere",
        "Kaga",
        "Kala/Balge",
        "Konduga",
        "Kukawa",
        "Kwaya Kusar",
        "Mafa",
        "Magumeri",
        "Maiduguri",
        "Marte",
        "Mobbar",
        "Monguno",
        "Ngala",
        "Nganzai",
        "Shani",
      ],
      "Cross River": [
        "Abi",
        "Akamkpa",
        "Akpabuyo",
        "Bakassi",
        "Bekwarra",
        "Biase",
        "Boki",
        "Calabar Municipal",
        "Calabar South",
        "Etung",
        "Ikom",
        "Obanliku",
        "Obubra",
        "Obudu",
        "Odukpani",
        "Ogoja",
        "Yakurr",
        "Yala",
      ],
      Delta: [
        "Aniocha North",
        "Aniocha South",
        "Bomadi",
        "Burutu",
        "Ethiope East",
        "Ethiope West",
        "Ika North East",
        "Ika South",
        "Isoko North",
        "Isoko South",
        "Ndokwa East",
        "Ndokwa West",
        "Okpe",
        "Oshimili North",
        "Oshimili South",
        "Patani",
        "Sapele",
        "Udu",
        "Ughelli North",
        "Ughelli South",
        "Ukwuani",
        "Uvwie",
        "Warri North",
        "Warri South",
        "Warri South West",
      ],
      Ebonyi: [
        "Abakaliki",
        "Afikpo North",
        "Afikpo South (Edda)",
        "Ebonyi",
        "Ezza North",
        "Ezza South",
        "Ikwo",
        "Ishielu",
        "Ivo",
        "Izzi",
        "Ohaozara",
        "Ohaukwu",
        "Onicha",
      ],
      Edo: [
        "Akoko-Edo",
        "Egor",
        "Esan Central",
        "Esan North-East",
        "Esan South-East",
        "Esan West",
        "Etsako Central",
        "Etsako East",
        "Etsako West",
        "Igueben",
        "Ikpoba-Okha",
        "Orhionmwon",
        "Oredo",
        "Ovia North-East",
        "Ovia South-West",
        "Owan East",
        "Owan West",
        "Uhunmwonde",
      ],
      Ekiti: [
        "Ado Ekiti",
        "Efon",
        "Ekiti East",
        "Ekiti South-West",
        "Ekiti West",
        "Emure",
        "Gbonyin",
        "Ido-Osi",
        "Ijero",
        "Ikere",
        "Ikole",
        "Ilejemeje",
        "Irepodun/Ifelodun",
        "Ise/Orun",
        "Moba",
        "Oye",
      ],
      Enugu: [
        "Aninri",
        "Awgu",
        "Enugu East",
        "Enugu North",
        "Enugu South",
        "Ezeagu",
        "Igbo Etiti",
        "Igbo Eze North",
        "Igbo Eze South",
        "Isi Uzo",
        "Nkanu East",
        "Nkanu West",
        "Nsukka",
        "Oji River",
        "Udenu",
        "Udi",
        "Uzo-Uwani",
      ],
      "FCT - Abuja": [
        "Abaji",
        "Bwari",
        "Gwagwalada",
        "Kuje",
        "Kwali",
        "Municipal Area Council",
      ],
      Gombe: [
        "Akko",
        "Balanga",
        "Billiri",
        "Dukku",
        "Funakaye",
        "Gombe",
        "Kaltungo",
        "Kwami",
        "Nafada",
        "Shongom",
        "Yamaltu/Deba",
      ],
      Imo: [
        "Aboh Mbaise",
        "Ahiazu Mbaise",
        "Ehime Mbano",
        "Ezinihitte",
        "Ideato North",
        "Ideato South",
        "Ihitte/Uboma",
        "Ikeduru",
        "Isiala Mbano",
        "Isu",
        "Mbaitoli",
        "Ngor Okpala",
        "Njaba",
        "Nkwerre",
        "Nwangele",
        "Obowo",
        "Oguta",
        "Ohaji/Egbema",
        "Okigwe",
        "Orlu",
        "Orsu",
        "Oru East",
        "Oru West",
        "Owerri Municipal",
        "Owerri North",
        "Owerri West",
        "Unuimo",
      ],
      Jigawa: [
        "Auyo",
        "Babura",
        "Biriniwa",
        "Birnin Kudu",
        "Buji",
        "Dutse",
        "Gagarawa",
        "Garki",
        "Gumel",
        "Guri",
        "Gwaram",
        "Gwiwa",
        "Hadejia",
        "Jahun",
        "Kafin Hausa",
        "Kaugama",
        "Kazaure",
        "Kiri Kasama",
        "Kiyawa",
        "Maigatari",
        "Malam Madori",
        "Miga",
        "Ringim",
        "Roni",
        "Sule Tankarkar",
        "Taura",
        "Yankwashi",
      ],
      Kaduna: [
        "Birnin Gwari",
        "Chikun",
        "Giwa",
        "Igabi",
        "Ikara",
        "Jaba",
        "Jema'a",
        "Kachia",
        "Kaduna North",
        "Kaduna South",
        "Kagarko",
        "Kajuru",
        "Kaura",
        "Kauru",
        "Kubau",
        "Kudan",
        "Lere",
        "Makarfi",
        "Sabon Gari",
        "Sanga",
        "Soba",
        "Zangon Kataf",
        "Zaria",
      ],
      Kano: [
        "Ajingi",
        "Albasu",
        "Bagwai",
        "Bebeji",
        "Bichi",
        "Bunkure",
        "Dala",
        "Dambatta",
        "Dawakin Kudu",
        "Dawakin Tofa",
        "Doguwa",
        "Fagge",
        "Gabasawa",
        "Garko",
        "Garun Mallam",
        "Gaya",
        "Gezawa",
        "Gwale",
        "Gwarzo",
        "Kabo",
        "Kano Municipal",
        "Karaye",
        "Kibiya",
        "Kiru",
        "Kumbotso",
        "Kunchi",
        "Kura",
        "Madobi",
        "Makoda",
        "Minjibir",
        "Nasarawa",
        "Rano",
        "Rimin Gado",
        "Rogo",
        "Shanono",
        "Sumaila",
        "Takai",
        "Tarauni",
        "Tofa",
        "Tsanyawa",
        "Tudun Wada",
        "Ungogo",
        "Warawa",
        "Wudil",
      ],
      Katsina: [
        "Bakori",
        "Batagarawa",
        "Batsari",
        "Baure",
        "Bindawa",
        "Charanchi",
        "Dandume",
        "Danja",
        "Dan Musa",
        "Daura",
        "Dutsi",
        "Dutsin-Ma",
        "Faskari",
        "Funtua",
        "Ingawa",
        "Jibia",
        "Kafur",
        "Kaita",
        "Kankara",
        "Kankia",
        "Katsina",
        "Kurfi",
        "Kusada",
        "Mai'Adua",
        "Malumfashi",
        "Mani",
        "Mashi",
        "Matazu",
        "Musawa",
        "Rimi",
        "Sabuwa",
        "Safana",
        "Sandamu",
        "Zango",
      ],
      Kebbi: [
        "Aleiro",
        "Arewa Dandi",
        "Argungu",
        "Augie",
        "Bagudo",
        "Birnin Kebbi",
        "Bunza",
        "Dandi",
        "Fakai",
        "Gwandu",
        "Jega",
        "Kalgo",
        "Koko/Besse",
        "Maiyama",
        "Ngaski",
        "Sakaba",
        "Shanga",
        "Suru",
        "Wasagu/Danko",
        "Yauri",
        "Zuru",
      ],
      Kogi: [
        "Adavi",
        "Ajaokuta",
        "Ankpa",
        "Bassa",
        "Dekina",
        "Ibaji",
        "Idah",
        "Igalamela-Odolu",
        "Ijumu",
        "Kabba/Bunu",
        "Kogi",
        "Lokoja",
        "Mopa-Muro",
        "Ofu",
        "Ogori/Magongo",
        "Okehi",
        "Okene",
        "Olamaboro",
        "Omala",
        "Yagba East",
        "Yagba West",
      ],
      Kwara: [
        "Asa",
        "Baruten",
        "Edu",
        "Ekiti",
        "Ifelodun",
        "Ilorin East",
        "Ilorin South",
        "Ilorin West",
        "Irepodun",
        "Isin",
        "Kaiama",
        "Moro",
        "Offa",
        "Oke Ero",
        "Oyun",
        "Pategi",
      ],
      Lagos: [
        "Agege",
        "Ajeromi-Ifelodun",
        "Alimosho",
        "Amuwo-Odofin",
        "Apapa",
        "Badagry",
        "Epe",
        "Eti-Osa",
        "Ibeju-Lekki",
        "Ifako-Ijaiye",
        "Ikeja",
        "Ikorodu",
        "Kosofe",
        "Lagos Island",
        "Lagos Mainland",
        "Mushin",
        "Ojo",
        "Oshodi-Isolo",
        "Shomolu",
        "Surulere",
      ],
      Nasarawa: [
        "Akwanga",
        "Awe",
        "Doma",
        "Karu",
        "Keana",
        "Keffi",
        "Kokona",
        "Lafia",
        "Nasarawa",
        "Nasarawa Egon",
        "Obi",
        "Toto",
        "Wamba",
      ],
      Niger: [
        "Agaie",
        "Agwara",
        "Bida",
        "Borgu",
        "Bosso",
        "Chanchaga",
        "Edati",
        "Gbako",
        "Gurara",
        "Katcha",
        "Kontagora",
        "Lapai",
        "Lavun",
        "Magama",
        "Mariga",
        "Mashegu",
        "Mokwa",
        "Moya",
        "Paikoro",
        "Rafi",
        "Rijau",
        "Shiroro",
        "Suleja",
        "Tafa",
        "Wushishi",
      ],
      Ogun: [
        "Abeokuta North",
        "Abeokuta South",
        "Ado-Odo/Ota",
        "Egbado North",
        "Egbado South",
        "Ewekoro",
        "Ifo",
        "Ijebu East",
        "Ijebu North",
        "Ijebu North East",
        "Ijebu Ode",
        "Ikenne",
        "Imeko Afon",
        "Ipokia",
        "Obafemi Owode",
        "Odeda",
        "Odogbolu",
        "Ogun Waterside",
        "Remo North",
        "Shagamu",
      ],
      Ondo: [
        "Akoko North-East",
        "Akoko North-West",
        "Akoko South-East",
        "Akoko South-West",
        "Akure North",
        "Akure South",
        "Ese Odo",
        "Idanre",
        "Ifedore",
        "Ilaje",
        "Ile Oluji/Okeigbo",
        "Irele",
        "Odigbo",
        "Okitipupa",
        "Ondo East",
        "Ondo West",
        "Ose",
        "Owo",
      ],
      Osun: [
        "Atakunmosa East",
        "Atakunmosa West",
        "Aiyedaade",
        "Aiyedire",
        "Boluwaduro",
        "Boripe",
        "Ede North",
        "Ede South",
        "Ife Central",
        "Ife East",
        "Ife North",
        "Ife South",
        "Egbedore",
        "Ejigbo",
        "Ifedayo",
        "Ifelodun",
        "Ila",
        "Ilesa East",
        "Ilesa West",
        "Irepodun",
        "Irewole",
        "Isokan",
        "Iwo",
        "Obokun",
        "Odo Otin",
        "Ola Oluwa",
        "Olorunda",
        "Oriade",
        "Orolu",
        "Osogbo",
      ],
      Oyo: [
        "Afijio",
        "Akinyele",
        "Atiba",
        "Atisbo",
        "Egbeda",
        "Ibadan North",
        "Ibadan North-East",
        "Ibadan North-West",
        "Ibadan South-East",
        "Ibadan South-West",
        "Ibarapa Central",
        "Ibarapa East",
        "Ibarapa North",
        "Ido",
        "Irepo",
        "Iseyin",
        "Itesiwaju",
        "Iwajowa",
        "Kajola",
        "Lagelu",
        "Ogbomosho North",
        "Ogbomosho South",
        "Ogo Oluwa",
        "Olorunsogo",
        "Oluyole",
        "Ona Ara",
        "Orelope",
        "Ori Ire",
        "Oyo East",
        "Oyo West",
        "Saki East",
        "Saki West",
        "Surulere",
      ],
      Plateau: [
        "Barkin Ladi",
        "Bassa",
        "Bokkos",
        "Jos East",
        "Jos North",
        "Jos South",
        "Kanam",
        "Kanke",
        "Langtang North",
        "Langtang South",
        "Mangu",
        "Mikang",
        "Pankshin",
        "Qua'an Pan",
        "Riyom",
        "Shendam",
        "Wase",
      ],
      Rivers: [
        "Abua/Odual",
        "Ahoada East",
        "Ahoada West",
        "Akuku-Toru",
        "Andoni",
        "Asari-Toru",
        "Bonny",
        "Degema",
        "Eleme",
        "Emuoha",
        "Etche",
        "Gokana",
        "Ikwerre",
        "Khana",
        "Obio/Akpor",
        "Ogba/Egbema/Ndoni",
        "Ogu/Bolo",
        "Okrika",
        "Omuma",
        "Opobo/Nkoro",
        "Oyigbo",
        "Port Harcourt",
        "Tai",
      ],
      Sokoto: [
        "Binji",
        "Bodinga",
        "Dange Shuni",
        "Gada",
        "Goronyo",
        "Gudu",
        "Gwadabawa",
        "Illela",
        "Isa",
        "Kebbe",
        "Kware",
        "Rabah",
        "Sabon Birni",
        "Shagari",
        "Silame",
        "Sokoto North",
        "Sokoto South",
        "Tambuwal",
        "Tangaza",
        "Tureta",
        "Wamako",
        "Wurno",
        "Yabo",
      ],
      Taraba: [
        "Ardo Kola",
        "Bali",
        "Donga",
        "Gashaka",
        "Gassol",
        "Ibi",
        "Jalingo",
        "Karim Lamido",
        "Kurmi",
        "Lau",
        "Sardauna",
        "Takum",
        "Ussa",
        "Wukari",
        "Yorro",
        "Zing",
      ],
      Yobe: [
        "Bade",
        "Bursari",
        "Damaturu",
        "Fika",
        "Fune",
        "Geidam",
        "Gujba",
        "Gulani",
        "Jakusko",
        "Karasuwa",
        "Machina",
        "Nangere",
        "Nguru",
        "Potiskum",
        "Tarmuwa",
        "Yunusari",
        "Yusufari",
      ],
      Zamfara: [
        "Anka",
        "Bakura",
        "Birnin Magaji/Kiyaw",
        "Bukkuyum",
        "Bungudu",
        "Gummi",
        "Gusau",
        "Kaura Namoda",
        "Maradun",
        "Maru",
        "Shinkafi",
        "Talata Mafara",
        "Chafe",
        "Zurmi",
      ],
    },
    "United States": {
      California: ["Los Angeles", "San Francisco", "San Diego", "Sacramento"],
      "New York": ["New York City", "Buffalo", "Rochester", "Albany"],
      Texas: ["Houston", "Dallas", "Austin", "San Antonio"],
    },
    Canada: {
      Ontario: ["Toronto", "Ottawa", "Mississauga", "Hamilton"],
      Quebec: ["Montreal", "Quebec City", "Laval", "Gatineau"],
      "British Columbia": ["Vancouver", "Victoria", "Surrey", "Burnaby"],
    },
  };

  function populateDropdown(selectElement, items, defaultOptionText) {
    selectElement.innerHTML = `<option value="">${defaultOptionText}</option>`;
    items.forEach((item) => {
      const option = document.createElement("option");
      option.value = item;
      option.textContent = item;
      selectElement.appendChild(option);
    });
    selectElement.disabled = false;
  }

  function resetDropdown(selectElement, defaultOptionText) {
    selectElement.innerHTML = `<option value="">${defaultOptionText}</option>`;
    selectElement.disabled = true;
  }

  function setupLocationDropdowns(countryId, stateId, lgaId) {
    const countrySelect = document.getElementById(countryId);
    const stateSelect = document.getElementById(stateId);
    const lgaSelect = document.getElementById(lgaId);

    if (!countrySelect || !stateSelect || !lgaSelect) return;

    populateDropdown(
      countrySelect,
      Object.keys(locationData),
      "Select Country"
    );

    countrySelect.addEventListener("change", function () {
      const selectedCountry = this.value;
      resetDropdown(lgaSelect, "Select LGA / City");
      if (selectedCountry && locationData[selectedCountry]) {
        populateDropdown(
          stateSelect,
          Object.keys(locationData[selectedCountry]),
          "Select State / Province"
        );
      } else {
        resetDropdown(stateSelect, "Select State / Province");
      }
    });

    stateSelect.addEventListener("change", function () {
      const selectedCountry = countrySelect.value;
      const selectedState = this.value;
      if (
        selectedCountry &&
        selectedState &&
        locationData[selectedCountry] &&
        locationData[selectedCountry][selectedState]
      ) {
        populateDropdown(
          lgaSelect,
          locationData[selectedCountry][selectedState],
          "Select LGA / City"
        );
      } else {
        resetDropdown(lgaSelect, "Select LGA / City");
      }
    });
  }

  setupLocationDropdowns("boSignupCountry", "boSignupState", "boSignupLGA");
  setupLocationDropdowns(
    "clientSignupCountry",
    "clientSignupState",
    "clientSignupLGA"
  );

  // --- Password Toggle Functionality ---
  function setupPasswordToggle() {
    const passwordWrappers = document.querySelectorAll(
      ".password-input-wrapper"
    );
    passwordWrappers.forEach((wrapper) => {
      const field = wrapper.querySelector(
        'input[type="password"], input[type="text"].is-revealed-password'
      );
      const toggleIcon = wrapper.querySelector(".password-toggle-icon");

      if (field && toggleIcon) {
        toggleIcon.addEventListener("click", function () {
          const isPassword = field.getAttribute("type") === "password";
          if (isPassword) {
            field.setAttribute("type", "text");
            field.classList.add("is-revealed-password");
            this.classList.remove("fa-eye-slash");
            this.classList.add("fa-eye");
            this.setAttribute("aria-pressed", "true");
            this.setAttribute("title", "Hide password");
          } else {
            field.setAttribute("type", "password");
            field.classList.remove("is-revealed-password");
            this.classList.remove("fa-eye");
            this.classList.add("fa-eye-slash");
            this.setAttribute("aria-pressed", "false");
            this.setAttribute("title", "Show password");
          }
        });
      }
    });
  }
  setupPasswordToggle();

  // Flash message auto-hide
  const flashMessagesContainer = document.querySelector(
    ".flash-messages-container"
  );
  if (flashMessagesContainer && flashMessagesContainer.children.length > 0) {
    setTimeout(() => {
      flashMessagesContainer.style.transition =
        "opacity 0.5s ease, transform 0.5s ease";
      flashMessagesContainer.style.opacity = "0";
      flashMessagesContainer.style.transform = "translateY(-20px)";
      setTimeout(() => {
        if (flashMessagesContainer.parentNode) {
          flashMessagesContainer.parentNode.removeChild(flashMessagesContainer);
        }
      }, 500);
    }, 7000);
  }

  // Set current year in footer
  const yearSpan = document.getElementById("currentYear");
  if (yearSpan) {
    yearSpan.textContent = new Date().getFullYear();
  }
});
