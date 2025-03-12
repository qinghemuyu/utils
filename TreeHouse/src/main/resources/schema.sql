-- 创建分享项目表
CREATE TABLE IF NOT EXISTS share_item (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE COMMENT '取件码',
    file_name VARCHAR(255) COMMENT '文件名称',
    text_content TEXT COMMENT '文本内容',
    file_path VARCHAR(255) COMMENT '文件路径',
    file_size BIGINT COMMENT '文件大小（字节）',
    type VARCHAR(10) NOT NULL COMMENT '分享类型：FILE或TEXT',
    remaining_count INT DEFAULT 10 COMMENT '剩余获取次数，默认10次',
    created_at DATETIME NOT NULL COMMENT '创建时间',
    expires_at DATETIME NOT NULL COMMENT '过期时间',
    INDEX idx_code (code),
    INDEX idx_expires_at (expires_at),
    INDEX idx_remaining_count (remaining_count)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分享项目表';