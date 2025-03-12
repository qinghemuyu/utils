package com.treehouse.heartbeatQh.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import javax.persistence.*;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Size;
import java.time.LocalDateTime;

@Entity
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ShareItem {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotBlank(message = "取件码不能为空")
    @Column(unique = true)
    private String code;

    private String fileName;

    @Size(max = 2000, message = "文本内容不能超过2000字")
    @Column(length = 2000)
    private String textContent;

    private String filePath;

    private Long fileSize;

    @Enumerated(EnumType.STRING)
    private ShareType type; // 枚举类型：FILE或TEXT

    private Integer remainingCount; // 剩余获取次数

    private LocalDateTime createdAt;

    private LocalDateTime expiresAt;

    // 预处理操作
    @PrePersist
    public void prePersist() {
        if (remainingCount == null) {
            remainingCount = 10; // 默认10次
        }
        createdAt = LocalDateTime.now();
        if (expiresAt == null) {
            expiresAt = createdAt.plusDays(7); // 默认7天过期
        }
    }
}