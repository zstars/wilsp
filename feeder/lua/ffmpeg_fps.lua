-----------------------------------
-- Redis FPS calc script: For ffmpeg / h264 mode.
-----------------------------------

local key_frames = redis.call('keys', 'wilsa:cams:cam*:stats:fps');

local total_fps = 0.0;
local total_fps_n = 0.0;
local ret = 0.0;


for _,k in ipairs(key_frames) do
  local cam_fps = tonumber(redis.call('get', k))
  total_fps = total_fps + cam_fps
  total_fps_n = total_fps_n + 1
end;

ret = total_fps / total_fps_n

print("AVERAGE ffmpeg FPS: ", ret)

return tostring(ret)