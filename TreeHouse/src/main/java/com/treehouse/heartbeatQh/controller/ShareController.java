package com.treehouse.heartbeatQh.controller;

import com.treehouse.heartbeatQh.model.ShareItem;
import com.treehouse.heartbeatQh.model.ShareType;
import com.treehouse.heartbeatQh.service.ShareService;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import java.io.IOException;
import java.net.MalformedURLException;
import java.nio.file.Path;
import java.nio.file.Paths;

@Controller
public class ShareController {

    private final ShareService shareService;

    public ShareController(ShareService shareService) {
        this.shareService = shareService;
    }

    /**
     * 首页
     */
    @GetMapping("/")
    public String index() {
        return "index";
    }

    /**
     * 文件上传页面
     */
    @GetMapping("/upload")
    public String uploadPage() {
        return "upload";
    }

    /**
     * 文本分享页面
     */
    @GetMapping("/text")
    public String textPage() {
        return "text";
    }

    /**
     * 处理文件上传
     */
    @PostMapping("/upload")
    public String handleFileUpload(@RequestParam("file") MultipartFile file,
                                  @RequestParam(value = "code", required = false) String code,
                                  @RequestParam(value = "expiryDays", required = false) Integer expiryDays,
                                  @RequestParam(value = "remainingCount", required = false) Integer remainingCount,
                                  RedirectAttributes redirectAttributes) {
        try {
            // 检查文件是否为空
            if (file.isEmpty()) {
                redirectAttributes.addFlashAttribute("error", "请选择要上传的文件");
                return "redirect:/upload";
            }

            // 创建文件分享
            ShareItem shareItem = shareService.createFileShare(file, code, expiryDays, remainingCount);

            // 添加成功消息
            redirectAttributes.addFlashAttribute("success", "文件上传成功！");
            redirectAttributes.addFlashAttribute("code", shareItem.getCode());
            return "redirect:/success";

        } catch (IOException e) {
            redirectAttributes.addFlashAttribute("error", "文件上传失败：" + e.getMessage());
            return "redirect:/upload";
        }
    }

    /**
     * 处理文本分享
     */
    @PostMapping("/text")
    public String handleTextShare(@RequestParam("textContent") String textContent,
                                @RequestParam(value = "code", required = false) String code,
                                @RequestParam(value = "expiryDays", required = false) Integer expiryDays,
                                @RequestParam(value = "remainingCount", required = false) Integer remainingCount,
                                RedirectAttributes redirectAttributes) {
        // 检查文本内容是否为空
        if (textContent == null || textContent.trim().isEmpty()) {
            redirectAttributes.addFlashAttribute("error", "请输入要分享的文本内容");
            return "redirect:/text";
        }

        // 创建文本分享
        ShareItem shareItem = shareService.createTextShare(textContent, code, expiryDays, remainingCount);

        // 添加成功消息
        redirectAttributes.addFlashAttribute("success", "文本分享成功！");
        redirectAttributes.addFlashAttribute("code", shareItem.getCode());
        return "redirect:/success";
    }

    /**
     * 成功页面
     */
    @GetMapping("/success")
    public String successPage() {
        return "success";
    }

    /**
     * 获取分享内容页面
     */
    @GetMapping("/get")
    public String getPage() {
        return "get";
    }

    /**
     * 处理获取分享内容
     */
    @PostMapping("/get")
    public String handleGetShare(@RequestParam("code") String code,
                               RedirectAttributes redirectAttributes) {
        try {
            // 检查取件码是否为空
            if (code == null || code.trim().isEmpty()) {
                redirectAttributes.addFlashAttribute("error", "请输入取件码");
                return "redirect:/get";
            }

            // 重定向到分享内容页面
            return "redirect:/share/" + code;

        } catch (Exception e) {
            redirectAttributes.addFlashAttribute("error", e.getMessage());
            return "redirect:/get";
        }
    }

    /**
     * 显示分享内容
     */
    @GetMapping("/share/{code}")
    public String viewShare(@PathVariable("code") String code, Model model) {
        try {
            // 获取分享内容
            ShareItem shareItem = shareService.getShareByCode(code);

            // 添加分享内容到模型
            model.addAttribute("shareItem", shareItem);

            return "view";

        } catch (Exception e) {
            model.addAttribute("error", e.getMessage());
            return "error";
        }
    }

    /**
     * 下载文件
     */
    @GetMapping("/download/{code}")
    public ResponseEntity<Resource> downloadFile(@PathVariable("code") String code) {
        try {
            // 获取分享内容
            ShareItem shareItem = shareService.getShareByCode(code);

            // 检查是否为文件类型
            if (shareItem.getType() != ShareType.FILE) {
                return ResponseEntity.badRequest().build();
            }

            // 获取文件路径
            Path filePath = Paths.get(shareItem.getFilePath());
            Resource resource = new UrlResource(filePath.toUri());

            // 检查文件是否存在
            if (!resource.exists()) {
                return ResponseEntity.notFound().build();
            }

            // 设置响应头
            return ResponseEntity.ok()
                    .contentType(MediaType.APPLICATION_OCTET_STREAM)
                    .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + shareItem.getFileName() + "\"")
                    .body(resource);

        } catch (Exception e) {
            return ResponseEntity.notFound().build();
        }
    }
}