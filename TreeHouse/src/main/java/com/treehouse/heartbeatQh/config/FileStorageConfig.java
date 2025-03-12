package com.treehouse.heartbeatQh.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

@Configuration
public class FileStorageConfig {

    @Value("${treehouse.file.upload-dir}")
    private String uploadDir;

    @Bean
    public CommandLineRunner initializeFileStorage() {
        return args -> {
            try {
                Path uploadPath = Paths.get(uploadDir);
                if (!Files.exists(uploadPath)) {
                    Files.createDirectories(uploadPath);
                    System.out.println("上传目录已创建: " + uploadPath.toAbsolutePath());
                } else {
                    System.out.println("上传目录已存在: " + uploadPath.toAbsolutePath());
                }
                
                // 确保目录有读写权限
                File directory = uploadPath.toFile();
                if (!directory.canRead() || !directory.canWrite()) {
                    directory.setReadable(true);
                    directory.setWritable(true);
                    System.out.println("已设置上传目录的读写权限");
                }
            } catch (Exception e) {
                System.err.println("创建上传目录时出错: " + e.getMessage());
                e.printStackTrace();
            }
        };
    }
}