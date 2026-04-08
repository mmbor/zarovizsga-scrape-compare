// =======================================
// Scraper creating .JSON for each subtopic
// Date: 2026-04-08
// Maximilian Marius Borka 
// =======================================

(async () => {
  const BASE_URL = "https://aok.zarovizsga.hu/zvb-service/methods/kerdesControl/getQuestionByLimit";
  
  // IF ENCOUNTERING ERRORS CONCIDER DECREASING
  const PAGE_SIZE = 1000;
  // I FIND ATLEAST 2 REQUIRED
  const MAX_RETRIES = 3;

  // SET LIST ACOORDING TO scraper_topicIDS.txt
  const topicMap = {
    "DENT": 142,
    "INT": 58,
    "OBGYN": 56,
    "ENT": 149,
    "PSYCH": 54,
    "RHEUM": 147,
    "URO": 146,
    "DERM": 143,
    "NEUR": 57,
    "OPTH": 144,
    "PED": 55,
    "PH": 60,
    "SURG": 59
  };

  // SET SUBJECTS TO THE IDs TO BE SCRAPED (see scraper_topicIDS.txt)
  const subjects = [142,58,56,149,54,147,146,143,57,144,55,60,59];

  for (const subjectId of subjects) {
    let allQuestions = [];
    let offset = 0;
    let page = 1;

    console.log(`Starting download for subject ID ${subjectId}...`);

    while (true) {
      let data = null;
      let retries = MAX_RETRIES;

      while (retries > 0) {
        try {
          const res = await fetch(BASE_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              feladatcsoport_id: subjectId,
              fejezet_id: null,
              tol: offset,
              darab: PAGE_SIZE,
              token: null
            })
          });

          const text = await res.text();
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          data = JSON.parse(text);
          break; // success
        } catch (err) {
          retries--;
          console.warn(`Error fetching subject ${subjectId} page ${page}: ${err.message}. Retries left: ${retries}`);
          if (retries === 0) {
            console.error(`Skipping subject ${subjectId} page ${page} after repeated errors.`);
            data = [];
            break;
          }
          await new Promise(r => setTimeout(r, 2000));
        }
      }

      if (!data || data.length === 0) break;

      allQuestions = allQuestions.concat(data);
      console.log(`Page ${page}: fetched ${data.length} questions (total: ${allQuestions.length})`);

      if (data.length < PAGE_SIZE) break;

      offset += PAGE_SIZE;
      page++;
      await new Promise(r => setTimeout(r, 300));
    }

    // Split questions by main number from csorszam
    const groups = {};
    allQuestions.forEach(q => {
      if (!q.csorszam) return;
      const match = q.csorszam.match(/(\d+)\./);
      const mainNum = match ? match[1] : "0";
      if (!groups[mainNum]) groups[mainNum] = [];
      groups[mainNum].push(q);
    });

    // Determine topic name for current subjectId
    const topicName = Object.keys(topicMap).find(key => topicMap[key] === subjectId) || "UNKNOWN";

    // Download each group as separate JSON
    for (const mainNum in groups) {
      const blob = new Blob([JSON.stringify(groups[mainNum], null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `zarovizsga_${topicName}_${subjectId}_${mainNum}.json`;
      a.click();
    }

    console.log(`Downloaded and split ${allQuestions.length} questions for subject ID ${subjectId}.`);
    await new Promise(r => setTimeout(r, 3000)); // delay between subjects
  }

  console.log("All  subjects downloaded and split.");
})();
