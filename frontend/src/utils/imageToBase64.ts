// 图片 Base64 转换工具

// 请和后台成员确认：后台要的是纯 Base64，还是带 data:image/... 前缀的完整字符串
// 当前默认返回带前缀的完整字符串
// 如果后台需要纯 Base64，可将 INCLUDE_DATA_PREFIX 改为 false
const INCLUDE_DATA_PREFIX = true;

export function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      if (INCLUDE_DATA_PREFIX) {
        resolve(result);
      } else {
        // 去掉 data:image/...;base64, 前缀
        const base64 = result.split(',')[1];
        resolve(base64);
      }
    };
    reader.onerror = () => {
      reject(new Error('照片读取失败'));
    };
    reader.readAsDataURL(file);
  });
}

// 支持的图片格式
export const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
export const ACCEPTED_IMAGE_EXTENSIONS = '.jpg,.jpeg,.png,.webp';

export function isAcceptedImageType(file: File): boolean {
  return ACCEPTED_IMAGE_TYPES.includes(file.type);
}
