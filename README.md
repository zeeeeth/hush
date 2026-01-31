# 🚇 Sensory-Safe Router

**A smarter way to navigate London for neurodiverse travelers.**

> *"For 20% of Londoners, the fastest route is the wrong route. Anxiety and sensory overload make the Tube inaccessible."*

## 🎯 What It Does

This app doesn't just find the fastest route—it finds the **calmest** one. We analyze TfL data to score routes based on:

- 📊 **Real-time crowding** at every station
- ⚠️ **Service disruptions** and delays  
- 🔄 **Number of interchanges** (stressful for many!)
- ⏰ **Time-based predictions** for crowding

## 🧮 The Algorithm

For each route option, we calculate a **Sensory Score**:

$$S = \sum_{stop \in R} (C_{stop} \times W_{type}) + P_{penalty}$$

Where:
- **C_stop** = Crowding level (0.0 to 1.0)
- **W_type** = Stress weight by activity type:
  - Platform waiting: 1.0 (highest)
  - Train travel: 0.6
  - Walking: 0.3
  - Interchanges: 0.8
- **P_penalty** = +50 for severe delays

## 🚀 Quick Start

### 1. Get a TfL API Key (Optional but Recommended)
- Go to [api-portal.tfl.gov.uk](https://api-portal.tfl.gov.uk)
- Register and create an app to get your API key
- Add it to `choochoo.py` in the `TFL_APP_KEY` variable

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the App
```bash
streamlit run choochoo.py
```

### 4. Open in Browser
Navigate to `http://localhost:8501`

## 🛠️ Tech Stack

- **Backend**: Python + Requests (TfL API integration)
- **Frontend**: Streamlit (rapid UI development)
- **Visualization**: Plotly (interactive charts)
- **Data**: Pandas (data manipulation)

## 📡 TfL APIs Used

| Endpoint | Purpose |
|----------|---------|
| `/Journey/JourneyResults/{from}/to/{to}` | Get route options |
| `/crowding/{NaptanID}` | Station crowding data |
| `/Line/Mode/tube,dlr/Status` | Real-time line status |
| `/StopPoint/Search` | Station search |

## 💡 Demo Script

**The Hook:**
> "For 20% of Londoners, the fastest route is the wrong route. Anxiety and sensory overload make the Tube inaccessible."

**Live Test:**
1. Enter `Bank` to `Oxford Circus` at 8:45 AM
2. Watch the app recommend a calmer route
3. See the crowding visualization for each option

**Tech Flex:**
> "We hit the TfL Crowding API for every single stop, calculated a dynamic congestion probability, and optimized for mental health, not just minutes."

## 📁 Project Structure

```
ichack26/
├── choochoo.py        # Main application
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## 🏆 Built for IC Hack 26

Solving accessibility for neurodiverse Londoners using data-driven decision making.

---

Made with 💙 for a calmer commute