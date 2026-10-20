import { API_BASE_URL } from '@/api/analyzeApi';

async function readResponse(response: Response) {
  if (!response.ok) throw new Error(`服务返回错误（${response.status}）`);
  return response.json();
}

function waitForNextPoll(signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) {
      reject(new DOMException('已取消', 'AbortError'));
      return;
    }
    const timer = window.setTimeout(() => {
      signal.removeEventListener('abort', cancel);
      resolve();
    }, 2000);
    function cancel() {
      window.clearTimeout(timer);
      reject(new DOMException('已取消', 'AbortError'));
    }
    signal.addEventListener('abort', cancel, { once: true });
  });
}

export async function uploadTryOnImage(image: string, signal: AbortSignal): Promise<string> {
  const upload = await readResponse(await fetch(`${API_BASE_URL}/api/upload`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image }),
    signal,
  }));
  if (typeof upload.file_id !== 'string' || !upload.file_id) throw new Error('照片上传后没有收到文件编号。');
  return upload.file_id;
}

export async function generateTryOn(fileId: string, templateId: string, kind: 'beard' | 'hair', signal: AbortSignal): Promise<string> {
  const task = await readResponse(await fetch(`${API_BASE_URL}/api/${kind}-try-on`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image: fileId, templateId }),
    signal,
  }));
  if (typeof task.task_id !== 'string' || !task.task_id) throw new Error('没有收到试戴任务编号。');

  for (let attempt = 0; attempt < 15; attempt += 1) {
    await waitForNextPoll(signal);
    const result = await readResponse(await fetch(`${API_BASE_URL}/api/task/${encodeURIComponent(task.task_id)}`, { signal }));
    if (result.status === 'success') {
      if (typeof result.url !== 'string' || !result.url) throw new Error('试戴已完成，但没有收到图片地址。');
      return result.url;
    }
    if (result.status === 'error') throw new Error('试戴图片生成失败，请重试。');
  }
  throw new Error('试戴图片生成超时，请重试。');
}
