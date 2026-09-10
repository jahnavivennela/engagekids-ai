import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import axios from "axios";

function Dashboard({ token, setToken }) {
  const navigate = useNavigate();
  const educatorId = 1;

  // Children
  const [children, setChildren] = useState([]);
  const [name, setName] = useState("");
  const [ageGroup, setAgeGroup] = useState("");
  const [interests, setInterests] = useState("");

  // Observations
  const [selectedChild, setSelectedChild] = useState(null);
  const [observations, setObservations] = useState([]);
  const [obsText, setObsText] = useState("");
  const [activity, setActivity] = useState("");
  const [skillNote, setSkillNote] = useState("");

  // Quick Activities
  const [quickActivityAgeGroup, setQuickActivityAgeGroup] = useState("3-4 years");
  const [quickActivityMood, setQuickActivityMood] = useState("Energetic and active");
  const [quickActivityMaterials, setQuickActivityMaterials] = useState("");
  const [quickActivityResult, setQuickActivityResult] = useState("");
  const [quickActivityLoading, setQuickActivityLoading] = useState(false);
    // Home Message
  const [homeMessageInput, setHomeMessageInput] = useState("");
  const [homeMessageResult, setHomeMessageResult] = useState("");
  const [homeMessageLoading, setHomeMessageLoading] = useState(false);

  const fetchChildren = async () => {
    try {
      const res = await axios.get(`http://127.0.0.1:8000/children/${educatorId}`);
      setChildren(res.data);
    } catch (err) {
      console.error("Failed to fetch children", err);
    }
  };

  useEffect(() => {
    fetchChildren();
  }, []);

  const handleAddChild = async (e) => {
    e.preventDefault();
    try {
      await axios.post("http://127.0.0.1:8000/children", {
        educator_id: educatorId,
        name,
        age_group: ageGroup,
        interests,
      });
      setName("");
      setAgeGroup("");
      setInterests("");
      fetchChildren();
    } catch (err) {
      console.error("Failed to add child", err);
    }
  };

  const fetchObservations = async (childId) => {
    try {
      const res = await axios.get(`http://127.0.0.1:8000/observations/${childId}`);
      setObservations(res.data);
    } catch (err) {
      console.error("Failed to fetch observations", err);
    }
  };

  const handleSelectChild = (child) => {
    setSelectedChild(child);
    fetchObservations(child.id);
  };

  const handleAddObservation = async (e) => {
    e.preventDefault();
    if (!selectedChild) return;
    try {
      await axios.post("http://127.0.0.1:8000/observations", {
        child_id: selectedChild.id,
        observation_text: obsText,
        activity: activity,
        skill_note: skillNote,
      });
      setObsText("");
      setActivity("");
      setSkillNote("");
      fetchObservations(selectedChild.id);
    } catch (err) {
      console.error("Failed to add observation", err);
    }
  };

  const handleGenerateQuickActivity = async () => {
    setQuickActivityLoading(true);
    setQuickActivityResult("");
    try {
      const res = await axios.post("http://127.0.0.1:8000/generate-quick-activity", {
        age_group: quickActivityAgeGroup,
        is_mixed: false,
        age_groups: [],
        mood: quickActivityMood,
        materials: quickActivityMaterials,
      });
      setQuickActivityResult(res.data.result);
    } catch (err) {
      console.error("Failed to generate quick activity", err);
      setQuickActivityResult("Something went wrong generating this — try again.");
    } finally {
      setQuickActivityLoading(false);
    }
  };
  const handleGenerateHomeMessage = async () => {
    setHomeMessageLoading(true);
    setHomeMessageResult("");
    try {
      const res = await axios.post("http://127.0.0.1:8000/generate-home-message", {
        activity_or_theme: homeMessageInput,
        languages: [],
      });
      setHomeMessageResult(res.data.result);
    } catch (err) {
      console.error("Failed to generate home message", err);
      setHomeMessageResult("Something went wrong generating this — try again.");
    } finally {
      setHomeMessageLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    setToken(null);
    navigate("/login");
  };

  return (
    <div style={{ maxWidth: 600, margin: "40px auto" }}>
      <div style={{ textAlign: "center" }}>
        <h1>🎨 Choose a tool</h1>
        <button onClick={handleLogout}>Log out</button>
      </div>

      <h2 style={{ marginTop: 40 }}>👤 Select Child</h2>
      <ul>
        {children.map((c) => (
          <li key={c.id} style={{ marginBottom: 6 }}>
            <button onClick={() => handleSelectChild(c)}>
              {c.name} — {c.age_group} — {c.interests}
            </button>
          </li>
        ))}
      </ul>

      <h3>Add a new child</h3>
      <form onSubmit={handleAddChild}>
        <input
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={{ display: "block", width: "100%", padding: 8, marginBottom: 8 }}
        />
        <input
          placeholder="Age group (e.g. 3-4 years)"
          value={ageGroup}
          onChange={(e) => setAgeGroup(e.target.value)}
          style={{ display: "block", width: "100%", padding: 8, marginBottom: 8 }}
        />
        <input
          placeholder="Interests"
          value={interests}
          onChange={(e) => setInterests(e.target.value)}
          style={{ display: "block", width: "100%", padding: 8, marginBottom: 8 }}
        />
        <button type="submit">Add child</button>
      </form>

      {selectedChild && (
        <>
          <h2 style={{ marginTop: 40 }}>📖 {selectedChild.name}'s History</h2>
          <ul>
            {observations.map((o) => (
              <li key={o.id} style={{ marginBottom: 10 }}>
                <strong>{o.obs_date}</strong> — {o.activity}
                <br />
                {o.observation_text}
                {o.skill_note && <div><em>Skill: {o.skill_note}</em></div>}
              </li>
            ))}
          </ul>

          <h3>Add an observation</h3>
          <form onSubmit={handleAddObservation}>
            <textarea
              placeholder="What did you observe?"
              value={obsText}
              onChange={(e) => setObsText(e.target.value)}
              style={{ display: "block", width: "100%", padding: 8, marginBottom: 8 }}
            />
            <input
              placeholder="Activity"
              value={activity}
              onChange={(e) => setActivity(e.target.value)}
              style={{ display: "block", width: "100%", padding: 8, marginBottom: 8 }}
            />
            <input
              placeholder="Skill note (optional)"
              value={skillNote}
              onChange={(e) => setSkillNote(e.target.value)}
              style={{ display: "block", width: "100%", padding: 8, marginBottom: 8 }}
            />
            <button type="submit">Save observation</button>
          </form>
        </>
      )}

      <h2 style={{ marginTop: 40 }}>⚡ Quick Activity Suggester</h2>

      <label>Age group</label>
      <select
        value={quickActivityAgeGroup}
        onChange={(e) => setQuickActivityAgeGroup(e.target.value)}
        style={{ display: "block", width: "100%", padding: 8, marginBottom: 8 }}
      >
        <option>0-6 months</option>
        <option>6-12 months</option>
        <option>1-2 years</option>
        <option>2-3 years</option>
        <option>3-4 years</option>
        <option>4-5 years</option>
      </select>

      <label>Mood right now</label>
      <select
        value={quickActivityMood}
        onChange={(e) => setQuickActivityMood(e.target.value)}
        style={{ display: "block", width: "100%", padding: 8, marginBottom: 8 }}
      >
        <option>Energetic and active</option>
        <option>Calm and focused</option>
        <option>Restless and unsettled</option>
        <option>Tired and low energy</option>
      </select>

      <input
        placeholder="Materials on hand (optional)"
        value={quickActivityMaterials}
        onChange={(e) => setQuickActivityMaterials(e.target.value)}
        style={{ display: "block", width: "100%", padding: 8, marginBottom: 8 }}
      />

      <button onClick={handleGenerateQuickActivity} disabled={quickActivityLoading}>
        {quickActivityLoading ? "Thinking of something quick..." : "⚡ Suggest Quick Activity"}
      </button>

      {quickActivityResult && (
        <div style={{ marginTop: 16, padding: 12, background: "#f0f0f0", borderRadius: 8, whiteSpace: "pre-wrap" }}>
          {quickActivityResult}
        </div>
      )}
      <h2 style={{ marginTop: 40 }}>🏠 Home Extension Message</h2>
      <textarea
        placeholder="What did the group do today (activity or theme)?"
        value={homeMessageInput}
        onChange={(e) => setHomeMessageInput(e.target.value)}
        style={{ display: "block", width: "100%", padding: 8, marginBottom: 8, minHeight: 70 }}
      />
      <button onClick={handleGenerateHomeMessage} disabled={homeMessageLoading}>
        {homeMessageLoading ? "Generating..." : "Generate Home Message"}
      </button>

      {homeMessageResult && (
        <div style={{ marginTop: 16, padding: 12, background: "#f0f0f0", borderRadius: 8, whiteSpace: "pre-wrap" }}>
          {homeMessageResult}
        </div>
      )}
    </div>
  );
}

export default Dashboard;