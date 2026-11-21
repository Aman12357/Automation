import React, { useEffect, useState } from 'react';
import { Activity, Clapperboard, Cloud, Database, ShieldCheck, Monitor, RefreshCw, Search } from 'lucide-react';

const API = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const CHANNEL_ID = 'UCX8pnu3DYUnx8qy8V_c6oHg';
function Stat({label,value,detail,icon:Icon}) {
  return <div className="stat"><div className="stat-head"><span>{label}</span><Icon size={18}/></div><strong>{value}</strong><small>{detail}</small></div>;
}
export default function App() {
  const [health,setHealth] = useState('checking');
  const [stats,setStats] = useState(null);
  const [error,setError] = useState('');
  const [busy,setBusy] = useState(false);
  const [discovering,setDiscovering] = useState(false);
  const [channel,setChannel] = useState(null);
  const [playlists,setPlaylists] = useState([]);
  const [metadataError,setMetadataError] = useState('');
  async function refresh() {
    setBusy(true); setError('');
    try {
      const [h,s] = await Promise.all([fetch(`${API}/api/health`),fetch(`${API}/api/dashboard`)]);
      if (!h.ok || !s.ok) throw new Error('API returned an error');
      const hj = await h.json(); const sj = await s.json();
      setHealth(hj.status); setStats(sj);
    } catch(e) { setHealth('offline'); setError(e.message); }
    finally { setBusy(false); }
  }
  async function seedChannel() {
    const response = await fetch(`${API}/api/channels/seed`,{method:'POST'});
    if (!response.ok) { setError('Could not register channel'); return; }
    refresh();
  }
  async function discoverMetadata() {
    setDiscovering(true); setMetadataError('');
    try {
      const [channelResponse,playlistResponse] = await Promise.all([
        fetch(`${API}/api/youtube/channels/${CHANNEL_ID}`),
        fetch(`${API}/api/youtube/channels/${CHANNEL_ID}/playlists`)
      ]);
      const channelJson = await channelResponse.json();
      const playlistJson = await playlistResponse.json();
      if (!channelResponse.ok) throw new Error(channelJson.detail || 'Channel metadata request failed');
      if (!playlistResponse.ok) throw new Error(playlistJson.detail || 'Playlist request failed');
      setChannel(channelJson); setPlaylists(playlistJson.items || []);
    } catch(e) { setMetadataError(e.message); }
    finally { setDiscovering(false); }
  }
  useEffect(()=>{refresh(); const id=setInterval(refresh,15000); return ()=>clearInterval(id)},[]);
  return <main className="shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-icon"><Clapperboard/></div><div><b>GTA SHORTS</b><small>AI FACTORY</small></div></div>
      <nav><a className="active">Overview</a><a>Creator Sources</a><a>Rights Registry</a><a>Worker Nodes</a><a>Processing Queue</a><a>Publishing</a><a>Settings</a></nav>
      <div className="side-note"><ShieldCheck size={17}/><span>Rights-first pipeline<br/><small>Publishing disabled</small></span></div>
    </aside>
    <section className="content">
      <header><div><p className="eyebrow">CONTROL CENTER / PHASE 02</p><h1>Automation overview</h1><p className="muted">Official YouTube metadata discovery and rights-first workflow.</p></div><button onClick={refresh} disabled={busy}><RefreshCw size={16}/> Refresh</button></header>
      <div className="status-row"><span className={`dot ${health==='ok'?'good':''}`}></span><b>API {health}</b><span className="muted">·</span><span className="muted">Local-first development</span><span className="push"></span><span className="pill">Publishing locked</span></div>
      {error && <div className="warning">Cannot reach API: {error}. Start the FastAPI server to load live status.</div>}
      <div className="stats">
        <Stat label="Monitored channels" value={stats?.channels ?? '—'} detail="Creator sources registered" icon={Cloud}/>
        <Stat label="Verified permissions" value={stats?.permissions_verified ?? '—'} detail={`${stats?.permissions_pending ?? 0} pending review`} icon={ShieldCheck}/>
        <Stat label="Queued jobs" value={stats?.jobs_queued ?? '—'} detail="Waiting for local worker" icon={Activity}/>
        <Stat label="Workers online" value={stats?.workers_online ?? '—'} detail="Windows processing nodes" icon={Monitor}/>
      </div>
      <div className="grid">
        <article className="panel wide"><div className="panel-title"><div><h2>Creator source</h2><p className="muted">Public channel and playlist metadata</p></div><span className="tag">Metadata only</span></div>
          <div className="source"><div className="channel-icon">YT</div><div className="source-info"><b>{channel?.title || 'Creator channel'}</b><span>{CHANNEL_ID}</span><small>https://www.youtube.com/channel/{CHANNEL_ID}</small></div></div>
          <p className="muted note">Discover public channel and playlist information through the official YouTube Data API. This does not download video or audio.</p>
          <div className="actions"><button className="primary" onClick={seedChannel}>Register channel</button><button onClick={discoverMetadata} disabled={discovering}><Search size={15}/>{discovering?'Checking…':'Discover metadata'}</button></div>
          {metadataError && <div className="warning metadata-warning">{metadataError}</div>}
          {channel && <div className="metadata-summary"><b>Channel metadata loaded</b><span>Uploads playlist: {channel.uploads_playlist_id || 'Not provided'}</span><span>Public subscribers: {channel.public_statistics?.subscriberCount || 'Hidden'}</span></div>}
          {playlists.length>0 && <div className="playlist-list"><b>Public playlists ({playlists.length})</b>{playlists.map(p=><div key={p.playlist_id}><span>{p.title}</span><small>{p.item_count} videos · {p.playlist_id}</small></div>)}</div>}
        </article>
        <article className="panel"><div className="panel-title"><div><h2>Hybrid infrastructure</h2><p className="muted">Cloud coordinator + Windows worker</p></div><Database/></div>
          <div className="infra-line"><Cloud/><div><b>Cloud control plane</b><small>API and database — local now</small></div><span className="tag">Ready</span></div>
          <div className="infra-line"><Monitor/><div><b>Windows worker</b><small>Heartbeat client included</small></div><span className="tag">Awaiting start</span></div>
        </article>
        <article className="panel wide"><h2>Safety gates</h2><div className="gate-list">
          <div><ShieldCheck/><span><b>Human rights review</b><small>Reviewer token + explicit editing, derivative and distribution rights</small></span><span className="locked">Enforced</span></div>
          <div><Clapperboard/><span><b>Media processing</b><small>Disabled until rights are independently verified</small></span><span className="locked">Locked</span></div>
          <div><Activity/><span><b>YouTube publishing</b><small>OAuth uploader not implemented</small></span><span className="locked">Locked</span></div>
        </div></article>
      </div>
      <footer>GTA Shorts AI Factory · Phase 2 · Metadata only · No footage downloaded or uploaded</footer>
    </section>
  </main>;
}
