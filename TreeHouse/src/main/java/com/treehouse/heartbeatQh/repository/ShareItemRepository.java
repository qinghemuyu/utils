package com.treehouse.heartbeatQh.repository;

import com.treehouse.heartbeatQh.model.ShareItem;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface ShareItemRepository extends JpaRepository<ShareItem, Long> {
    
    // 根据取件码查找分享项
    Optional<ShareItem> findByCode(String code);
    
    // 查找所有过期的分享项
    List<ShareItem> findByExpiresAtBefore(LocalDateTime now);
    
    // 查找所有剩余次数为0的分享项
    List<ShareItem> findByRemainingCountLessThanEqual(Integer count);
    
    // 减少剩余获取次数
    @Modifying
    @Query("UPDATE ShareItem s SET s.remainingCount = s.remainingCount - 1 WHERE s.id = ?1")
    void decrementRemainingCount(Long id);
    
    // 检查取件码是否已存在
    boolean existsByCode(String code);
}