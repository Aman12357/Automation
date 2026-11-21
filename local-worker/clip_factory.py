"""Rights-gated local vertical clip renderer. Does not download or upload media."""
import argparse, json, shutil, subprocess, sys
from pathlib import Path

FORMATS={".mp4",".mov",".mkv",".webm",".m4v"}

def command(args, capture=False):
    return subprocess.run(args,check=True,text=True,stdout=subprocess.PIPE if capture else subprocess.DEVNULL,stderr=subprocess.PIPE if capture else subprocess.DEVNULL)

def duration(path):
    return float(command(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(path)],True).stdout.strip())

def check_rights(folder, source, commercial):
    manifest=folder/"rights_manifest.json"
    if not manifest.is_file(): raise ValueError("rights_manifest.json is missing")
    data=json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("status")!="verified": raise ValueError("manifest status must be verified")
    for key in ("editing_allowed","derivative_allowed","distribution_allowed"):
        if data.get(key) is not True: raise ValueError(f"{key} must be true")
    if commercial and data.get("commercial_allowed") is not True: raise ValueError("commercial rights are not granted")
    if not str(data.get("rights_holder","")).strip(): raise ValueError("rights_holder is required")
    if not str(data.get("evidence_reference","")).strip(): raise ValueError("evidence_reference is required")
    if data.get("source_file") and Path(data["source_file"]).name!=source.name: raise ValueError("source_file does not match")
    return data

def audio_score(source,start,length):
    args=["ffmpeg","-hide_banner","-nostats","-ss",str(start),"-t",str(length),"-i",str(source),"-vn","-af","volumedetect","-f","null","-"]
    p=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if p.returncode: raise RuntimeError("FFmpeg audio analysis failed")
    for line in p.stderr.splitlines():
        if "mean_volume:" in line:
            try: return float(line.split("mean_volume:")[1].split("dB")[0].strip())
            except ValueError: pass
    return -99.0

def candidates(source,total,clip_len,step,count):
    if total<=clip_len: return [(0.0,total,audio_score(source,0,total))]
    scored=[]
    for start in range(0,int(total-clip_len)+1,step):
        scored.append((float(start),float(clip_len),audio_score(source,start,clip_len)))
    picked=[]
    for item in sorted(scored,key=lambda x:x[2],reverse=True):
        a,n,_=item
        if all(a+n<=b or b+m<=a for b,m,_ in picked): picked.append(item)
        if len(picked)>=count: break
    return sorted(picked)

def render(source,out,start,length):
    out.parent.mkdir(parents=True,exist_ok=True)
    graph="[0:v]split=2[bg][fg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=22:10[blur];[fg]scale=1080:1920:force_original_aspect_ratio=decrease[main];[blur][main]overlay=(W-w)/2:(H-h)/2,setsar=1[v]"
    command(["ffmpeg","-y","-hide_banner","-loglevel","error","-ss",f"{start:.3f}","-i",str(source),"-t",f"{length:.3f}","-filter_complex",graph,"-map","[v]","-map","0:a?","-c:v","libx264","-preset","veryfast","-crf","21","-c:a","aac","-b:a","160k","-pix_fmt","yuv420p","-movflags","+faststart",str(out)])

def main():
    p=argparse.ArgumentParser(description="Generate draft Shorts from rights-cleared local files")
    p.add_argument("--inbox",default="../media/inbox"); p.add_argument("--output",default="../media/ready")
    p.add_argument("--clips-per-source",type=int,default=5); p.add_argument("--clip-seconds",type=int,default=30)
    p.add_argument("--step-seconds",type=int,default=10); p.add_argument("--commercial",action="store_true")
    p.add_argument("--process",action="store_true",help="Render files; omit for dry-run planning")
    a=p.parse_args()
    if a.clips_per_source<1 or not 5<=a.clip_seconds<=60 or a.step_seconds<1: p.error("Invalid clip count, duration or step")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        print("ERROR: ffmpeg and ffprobe must be installed and available on PATH"); return 2
    inbox=Path(a.inbox).resolve(); output=Path(a.output).resolve()
    if not inbox.is_dir(): print(f"Inbox not found: {inbox}"); return 0
    accepted=0
    for folder in sorted(x for x in inbox.iterdir() if x.is_dir()):
        sources=[x for x in folder.iterdir() if x.is_file() and x.suffix.lower() in FORMATS]
        if len(sources)!=1: 
            if sources: print(f"BLOCKED {folder.name}: expected one media file")
            continue
        source=sources[0]
        try:
            rights=check_rights(folder,source,a.commercial); total=duration(source)
            picks=candidates(source,total,a.clip_seconds,a.step_seconds,a.clips_per_source)
            print(f"APPROVED FOR DRAFTING: {source.name} | rights holder: {rights['rights_holder']}")
            for i,(start,length,score) in enumerate(picks,1):
                target=output/folder.name/f"short_{i:02d}.mp4"
                print(f"Candidate {i}: {start:.1f}s, audio mean {score:.1f} dB")
                if a.process: render(source,target,start,length); print(f"Rendered: {target}")
            accepted+=1
        except (ValueError,OSError,RuntimeError,subprocess.CalledProcessError,json.JSONDecodeError) as e:
            print(f"BLOCKED {folder.name}: {e}")
    print(f"Sources accepted: {accepted}; mode: {'RENDER' if a.process else 'DRY RUN'}")
    return 0

if __name__=="__main__": sys.exit(main())
