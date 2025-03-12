package com.treehouse.heartbeatQh.service;

import com.treehouse.heartbeatQh.exception.ResourceNotFoundException;
import com.treehouse.heartbeatQh.model.ShareItem;
import com.treehouse.heartbeatQh.model.ShareType;
import com.treehouse.heartbeatQh.repository.ShareItemRepository;
import org.apache.commons.io.FilenameUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.Random;
import java.util.UUID;

@Service
public class ShareService {

    private final ShareItemRepository shareItemRepository;
    
    @Value("${treehouse.file.upload-dir}")
    private String uploadDir;
    
    public ShareService(ShareItemRepository shareItemRepository) {
        this.shareItemRepository = shareItemRepository;
    }
    
    /**
     * 创建文件分享
     */
    @Transactional
    public ShareItem createFileShare(MultipartFile file, String code, Integer expiryDays, Integer remainingCount) throws IOException {
        // 检查目录是否存在，不存在则创建
        File directory = new File(uploadDir);
        if (!directory.exists()) {
            directory.mkdirs();
        }
        
        // 生成唯一文件名
        String originalFilename = file.getOriginalFilename();
        String extension = FilenameUtils.getExtension(originalFilename);
        String newFilename = UUID.randomUUID().toString() + "." + extension;
        
        // 保存文件
        Path filePath = Paths.get(uploadDir, newFilename);
        Files.copy(file.getInputStream(), filePath);
        
        // 创建分享项
        ShareItem shareItem = new ShareItem();
        shareItem.setCode(code == null || code.isEmpty() ? generateRandomCode() : code);
        shareItem.setFileName(originalFilename);
        shareItem.setFilePath(filePath.toString());
        shareItem.setFileSize(file.getSize());
        shareItem.setType(ShareType.FILE);
        
        // 设置过期时间
        if (expiryDays != null) {
            if (expiryDays == -1) {
                // 永久有效，设置为100年后
                shareItem.setExpiresAt(LocalDateTime.now().plusYears(100));
            } else {
                shareItem.setExpiresAt(LocalDateTime.now().plusDays(expiryDays));
            }
        }
        
        // 设置可获取次数
        if (remainingCount != null) {
            shareItem.setRemainingCount(remainingCount);
        }
        
        return shareItemRepository.save(shareItem);
    }
    
    /**
     * 创建文本分享
     */
    @Transactional
    public ShareItem createTextShare(String textContent, String code, Integer expiryDays, Integer remainingCount) {
        ShareItem shareItem = new ShareItem();
        shareItem.setCode(code == null || code.isEmpty() ? generateRandomCode() : code);
        shareItem.setTextContent(textContent);
        shareItem.setType(ShareType.TEXT);
        
        // 设置过期时间
        if (expiryDays != null) {
            if (expiryDays == -1) {
                // 永久有效，设置为100年后
                shareItem.setExpiresAt(LocalDateTime.now().plusYears(100));
            } else {
                shareItem.setExpiresAt(LocalDateTime.now().plusDays(expiryDays));
            }
        }
        
        // 设置可获取次数
        if (remainingCount != null) {
            shareItem.setRemainingCount(remainingCount);
        }
        
        return shareItemRepository.save(shareItem);
    }
    
    /**
     * 获取分享内容
     */
    @Transactional
    public ShareItem getShareByCode(String code) {
        ShareItem shareItem = shareItemRepository.findByCode(code)
                .orElseThrow(() -> new ResourceNotFoundException("未找到该取件码对应的分享内容"));
        
        // 检查是否过期
        if (shareItem.getExpiresAt().isBefore(LocalDateTime.now())) {
            throw new ResourceNotFoundException("该分享内容已过期");
        }
        
        // 检查剩余次数
        if (shareItem.getRemainingCount() <= 0) {
            throw new ResourceNotFoundException("该分享内容已达到最大获取次数");
        }
        
        // 减少剩余次数
        shareItemRepository.decrementRemainingCount(shareItem.getId());
        shareItem.setRemainingCount(shareItem.getRemainingCount() - 1);
        
        return shareItem;
    }
    
    /**
     * 生成随机取件码
     * 取件码以QH开头，长度在6-18位之间
     */
    private String generateRandomCode() {
        String chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        StringBuilder code = new StringBuilder("QH"); // 固定前缀为QH
        Random random = new Random();
        
        // 生成随机长度的取件码（总长度在6-18位之间，已有前缀QH，所以随机部分长度为4-16位）
        int randomLength = 4 + random.nextInt(13); // 4到16之间的随机数
        
        // 生成随机码
        for (int i = 0; i < randomLength; i++) {
            code.append(chars.charAt(random.nextInt(chars.length())));
        }
        
        // 检查是否已存在，如果存在则重新生成
        if (shareItemRepository.existsByCode(code.toString())) {
            return generateRandomCode();
        }
        
        return code.toString();
    }
    
    /**
     * 清理过期或已达到最大获取次数的分享内容
     */
    @Transactional
    public void cleanupExpiredShares() {
        LocalDateTime now = LocalDateTime.now();
        
        // 查找过期的分享项
        List<ShareItem> expiredItems = shareItemRepository.findByExpiresAtBefore(now);
        
        // 查找已达到最大获取次数的分享项
        List<ShareItem> usedItems = shareItemRepository.findByRemainingCountLessThanEqual(0);
        
        // 合并两个列表
        expiredItems.addAll(usedItems);
        
        // 删除文件
        for (ShareItem item : expiredItems) {
            if (item.getType() == ShareType.FILE && item.getFilePath() != null) {
                try {
                    Files.deleteIfExists(Paths.get(item.getFilePath()));
                } catch (IOException e) {
                    // 记录日志但不中断处理
                    System.err.println("删除文件失败: " + item.getFilePath());
                }
            }
        }
        
        // 从数据库中删除
        shareItemRepository.deleteAll(expiredItems);
    }
}