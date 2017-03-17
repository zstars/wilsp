-----------------------------------
-- Redis FPS calc script
-----------------------------------

local key_frames = redis.call('keys', 'wilsa:cams:cam*:stats:cycle_frames');

local total_fps = 0.0;
local total_fps_n = 0.0;
local ret = 0.0;


for _,k in ipairs(key_frames) do
  local frames = tonumber(redis.call('get', k))
  local elapsed_key = string.gsub(k, 'cycle_frames', 'cycle_elapsed')
  local elapsed = tonumber(redis.call('get', elapsed_key))
  local cam_fps = frames / elapsed
  --redis.log(redis.LOG_ERROR, 'ok')
  print(cam_fps)
  ret = cam_fps

  total_fps = total_fps + cam_fps
  total_fps_n = total_fps_n + 1
end;

ret = total_fps / total_fps_n

print("AVERAGE FPS: ", ret)

return tostring(ret)