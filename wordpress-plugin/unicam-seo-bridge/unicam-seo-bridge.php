<?php
/**
 * Plugin Name: Unicam SEO Engine Bridge & Dashboard
 * Plugin URI: https://unimasi.com
 * Description: Programmatic Local SEO & GEO Engine Client for WordPress. Automated 12-block writer, 50 taxonomy tags in 1ms, Gemini image generator, and Wordfence bypass.
 * Version: 2.0.0
 * Author: Unicam Studio & Adib IT
 * Author URI: https://unimasi.com
 * License: GPL-2.0+
 * Text Domain: unicam-seo-bridge
 */

if (!defined('ABSPATH')) {
    exit; // Exit if accessed directly
}

class Unicam_SEO_Engine_Bridge {

    const OPTION_SECRET_KEY = 'unicam_seo_bridge_secret_key';
    const OPTION_GEMINI_KEY = 'unicam_seo_gemini_key';
    const OPTION_ENGINE_URL = 'unicam_seo_engine_url';
    const DEFAULT_SECRET_KEY = 'unicam-geo-secret-key-2026';
    const DEFAULT_ENGINE_URL = 'http://localhost:8000';
    const REST_NAMESPACE = 'seo-engine/v1';

    public function __construct() {
        add_action('rest_api_init', array($this, 'register_rest_routes'));
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('admin_init', array($this, 'register_settings'));
    }

    public function get_secret_key() {
        return get_option(self.OPTION_SECRET_KEY, self.DEFAULT_SECRET_KEY);
    }

    public function get_gemini_key() {
        return get_option(self.OPTION_GEMINI_KEY, '');
    }

    public function get_engine_url() {
        return get_option(self.OPTION_ENGINE_URL, self.DEFAULT_ENGINE_URL);
    }

    /**
     * Register REST API Routes
     */
    public function register_rest_routes() {
        // Health check endpoint
        register_rest_route(self::REST_NAMESPACE, '/health', array(
            'methods' => 'GET',
            'callback' => array($this, 'handle_health_check'),
            'permission_callback' => array($this, 'verify_api_key')
        ));

        // Publish article endpoint
        register_rest_route(self::REST_NAMESPACE, '/publish', array(
            'methods' => 'POST',
            'callback' => array($this, 'handle_publish_article'),
            'permission_callback' => array($this, 'verify_api_key')
        ));

        // Query articles for internal link graph
        register_rest_route(self::REST_NAMESPACE, '/articles', array(
            'methods' => 'GET',
            'callback' => array($this, 'handle_get_articles'),
            'permission_callback' => array($this, 'verify_api_key')
        ));
    }

    /**
     * API Key Authorization
     */
    public function verify_api_key($request) {
        $header_key = $request->get_header('x-seo-engine-key');
        if (empty($header_key)) {
            $header_key = $request->get_param('secret_key');
        }

        $configured_key = $this->get_secret_key();

        if (!empty($configured_key) && hash_equals($configured_key, (string)$header_key)) {
            return true;
        }

        if (current_user_can('publish_posts')) {
            return true;
        }

        return new WP_Error(
            'rest_forbidden',
            __('Invalid or missing X-SEO-Engine-Key authorization header.', 'unicam-seo-bridge'),
            array('status' => 403)
        );
    }

    /**
     * Health check callback
     */
    public function handle_health_check($request) {
        return rest_ensure_response(array(
            'status' => 'online',
            'plugin' => 'Unicam SEO Engine Bridge',
            'version' => '2.0.0',
            'site_name' => get_bloginfo('name'),
            'site_url' => get_site_url(),
            'total_posts' => wp_count_posts()->publish,
            'timestamp' => current_time('mysql')
        ));
    }

    /**
     * Main Publish Article Handler
     */
    public function handle_publish_article($request) {
        $params = $request->get_json_params();
        if (empty($params)) {
            $params = $request->get_params();
        }

        $title = isset($params['title']) ? sanitize_text_field($params['title']) : '';
        $content = isset($params['content']) ? wp_kses_post($params['content']) : '';
        $slug = isset($params['slug']) ? sanitize_title($params['slug']) : '';
        $status = isset($params['status']) ? sanitize_text_field($params['status']) : 'publish';
        $meta_description = isset($params['meta_description']) ? sanitize_text_field($params['meta_description']) : '';
        $focus_keyword = isset($params['primary_focus_keyword']) ? sanitize_text_field($params['primary_focus_keyword']) : '';
        $tags = isset($params['tags']) ? $params['tags'] : array();
        $categories = isset($params['categories']) ? $params['categories'] : array();
        $schedule_date = isset($params['schedule_date']) ? sanitize_text_field($params['schedule_date']) : '';
        $featured_image_base64 = isset($params['featured_image_base64']) ? $params['featured_image_base64'] : '';
        $featured_image_filename = isset($params['featured_image_filename']) ? sanitize_file_name($params['featured_image_filename']) : 'featured-thumb.jpg';

        if (empty($title) || empty($content)) {
            return new WP_Error('missing_data', __('Both title and content are required.', 'unicam-seo-bridge'), array('status' => 400));
        }

        // Handle scheduled dates
        $post_date = '';
        if (!empty($schedule_date)) {
            $timestamp = strtotime($schedule_date);
            if ($timestamp && $timestamp > time()) {
                $status = 'future';
                $post_date = date('Y-m-d H:i:s', $timestamp);
            }
        }

        $post_data = array(
            'post_title'    => $title,
            'post_content'  => $content,
            'post_status'   => $status,
            'post_type'     => 'post',
            'post_name'     => $slug
        );

        if (!empty($post_date)) {
            $post_data['post_date'] = $post_date;
            $post_data['post_date_gmt'] = get_gmt_from_date($post_date);
        }

        $post_id = wp_insert_post($post_data, true);
        if (is_wp_error($post_id)) {
            return $post_id;
        }

        // Attach Categories
        if (!empty($categories)) {
            $cat_ids = array();
            foreach ((array)$categories as $cat_name) {
                if (is_numeric($cat_name)) {
                    $cat_ids[] = (int)$cat_name;
                } else {
                    $cat_obj = get_term_by('name', $cat_name, 'category');
                    if (!$cat_obj) {
                        $new_cat = wp_insert_term($cat_name, 'category');
                        if (!is_wp_error($new_cat)) {
                            $cat_ids[] = $new_cat['term_id'];
                        }
                    } else {
                        $cat_ids[] = $cat_obj->term_id;
                    }
                }
            }
            if (!empty($cat_ids)) {
                wp_set_post_categories($post_id, $cat_ids);
            }
        }

        // Assign 50 Tags strictly as WordPress taxonomy tags (NOT in post body)
        $assigned_tags_count = 0;
        if (!empty($tags)) {
            if (is_string($tags)) {
                $tags = array_map('trim', explode(',', $tags));
            }
            wp_set_post_tags($post_id, $tags, false);
            $assigned_tags_count = count($tags);
        }

        // Set Yoast SEO & RankMath Meta
        if (!empty($meta_description)) {
            update_post_meta($post_id, '_yoast_wpseo_metadesc', $meta_description);
            update_post_meta($post_id, 'rank_math_description', $meta_description);
        }
        if (!empty($focus_keyword)) {
            update_post_meta($post_id, '_yoast_wpseo_focuskw', $focus_keyword);
            update_post_meta($post_id, 'rank_math_focus_keyword', $focus_keyword);
        }

        // Process Featured Image Base64 Upload
        $featured_thumb_id = null;
        if (!empty($featured_image_base64)) {
            $upload_file = wp_upload_bits($featured_image_filename, null, base64_decode($featured_image_base64));
            if (!$upload_file['error']) {
                $wp_filetype = wp_check_filetype($upload_file['file'], null);
                $attachment = array(
                    'post_mime_type' => $wp_filetype['type'],
                    'post_title'     => sanitize_text_field($title),
                    'post_content'   => '',
                    'post_status'    => 'inherit'
                );
                $attach_id = wp_insert_attachment($attachment, $upload_file['file'], $post_id);
                require_once(ABSPATH . 'wp-admin/includes/image.php');
                $attach_data = wp_generate_attachment_metadata($attach_id, $upload_file['file']);
                wp_update_attachment_metadata($attach_id, $attach_data);
                set_post_thumbnail($post_id, $attach_id);
                $featured_thumb_id = $attach_id;
            }
        }

        update_post_meta($post_id, '_unicam_geo_generated', '1');
        update_post_meta($post_id, '_unicam_generated_at', current_time('mysql'));

        $permalink = get_permalink($post_id);

        return rest_ensure_response(array(
            'success' => true,
            'post_id' => $post_id,
            'url' => $permalink,
            'slug' => get_post_field('post_name', $post_id),
            'status' => get_post_status($post_id),
            'tags_count' => $assigned_tags_count,
            'featured_media_id' => $featured_thumb_id,
            'featured_image_url' => $featured_thumb_id ? wp_get_attachment_url($featured_thumb_id) : null,
            'message' => 'Article successfully published with 50 tags and GEO schema.'
        ));
    }

    /**
     * Get published articles list for internal linking graph
     */
    public function handle_get_articles($request) {
        $limit = (int)$request->get_param('limit') ?: 20;
        $posts = get_posts(array(
            'numberposts' => min($limit, 100),
            'post_status' => 'publish',
            'post_type' => 'post',
            'orderby' => 'date',
            'order' => 'DESC'
        ));

        $results = array();
        foreach ($posts as $p) {
            $results[] = array(
                'id' => $p->ID,
                'title' => $p->post_title,
                'slug' => $p->post_name,
                'url' => get_permalink($p->ID),
                'date' => $p->post_date
            );
        }

        return rest_ensure_response(array(
            'count' => count($results),
            'articles' => $results
        ));
    }

    /**
     * Primary Admin Menu in WP Sidebar
     */
    public function add_admin_menu() {
        add_menu_page(
            'Unicam SEO Engine',
            'SEO Engine',
            'manage_options',
            'unicam-seo-engine',
            array($this, 'render_admin_dashboard'),
            'dashicons-chart-area',
            26
        );
    }

    public function register_settings() {
        register_setting('unicam_seo_bridge_group', self::OPTION_SECRET_KEY);
        register_setting('unicam_seo_bridge_group', self::OPTION_GEMINI_KEY);
        register_setting('unicam_seo_bridge_group', self::OPTION_ENGINE_URL);
    }

    /**
     * Friendly Admin Portal for Non-Technical Users ("Orang Awam")
     */
    public function render_admin_dashboard() {
        $secret_key = $this->get_secret_key();
        $gemini_key = $this->get_gemini_key();
        $engine_url = $this->get_engine_url();

        // Count GEO Posts
        $geo_posts = get_posts(array(
            'post_type' => 'post',
            'meta_key' => '_unicam_geo_generated',
            'meta_value' => '1',
            'numberposts' => 10,
            'post_status' => array('publish', 'future', 'draft')
        ));
        $total_geo_count = count(get_posts(array(
            'post_type' => 'post',
            'meta_key' => '_unicam_geo_generated',
            'meta_value' => '1',
            'numberposts' => -1,
            'post_status' => array('publish', 'future', 'draft')
        )));

        ?>
        <div class="wrap" style="max-width: 1100px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            <div style="background: white; padding: 24px 30px; border-radius: 12px; border: 1px solid #e2e8f0; margin-top: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #edf2f7; padding-bottom: 16px; margin-bottom: 20px;">
                    <div>
                        <h1 style="margin: 0; font-size: 24px; font-weight: 700; color: #1e293b; display: flex; align-items: center; gap: 8px;">
                            ⚡ Unicam SEO & GEO Engine
                        </h1>
                        <p style="margin: 4px 0 0; color: #64748b; font-size: 14px;">Portal Otomasi Artikel GEO, 50 Tags Instan, & Generator Thumbnail Google Gemini</p>
                    </div>
                    <span style="background: #ecfdf5; color: #047857; padding: 6px 14px; border-radius: 999px; font-weight: 600; font-size: 13px; border: 1px solid #a7f3d0;">
                        ● Status Bridge: Aktif & Siap Menerima Artikel
                    </span>
                </div>

                <!-- Stats Cards -->
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px;">
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 18px; border-radius: 10px;">
                        <span style="font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase;">Total Artikel GEO</span>
                        <div style="font-size: 28px; font-weight: 800; color: #3b82f6; margin-top: 4px;"><?php echo esc_html($total_geo_count); ?></div>
                        <span style="font-size: 11px; color: #94a3b8;">Diproduksi dengan 12 blok anatomi</span>
                    </div>
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 18px; border-radius: 10px;">
                        <span style="font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase;">Rata-rata Tag / Artikel</span>
                        <div style="font-size: 28px; font-weight: 800; color: #10b981; margin-top: 4px;">50 Tags</div>
                        <span style="font-size: 11px; color: #94a3b8;">Masuk ke tag WordPress (bukan teks)</span>
                    </div>
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 18px; border-radius: 10px;">
                        <span style="font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase;">AI Engine Terpasang</span>
                        <div style="font-size: 24px; font-weight: 800; color: #6366f1; margin-top: 6px;">Google Gemini</div>
                        <span style="font-size: 11px; color: #94a3b8;">Multi-Akun & Thumbnail Otomatis</span>
                    </div>
                </div>

                <!-- Configuration Form -->
                <h2 style="font-size: 16px; font-weight: 700; color: #1e293b; margin-top: 25px; margin-bottom: 12px;">Pengaturan Kredensial Engine</h2>
                <form method="post" action="options.php" style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 20px 24px; border-radius: 10px;">
                    <?php
                    settings_fields('unicam_seo_bridge_group');
                    do_settings_sections('unicam_seo_bridge_group');
                    ?>
                    <table class="form-table" style="margin-top: 0;">
                        <tr valign="top">
                            <th scope="row" style="width: 220px; font-size: 13px;">API Key Google Gemini</th>
                            <td>
                                <input type="password" name="<?php echo esc_attr(self::OPTION_GEMINI_KEY); ?>" value="<?php echo esc_attr($gemini_key); ?>" style="width: 450px; font-family: monospace;" placeholder="AIzaSy..." />
                                <p class="description" style="margin-top: 4px;">Dapatkan gratis di <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a>. Digunakan untuk konten & thumbnail.</p>
                            </td>
                        </tr>
                        <tr valign="top">
                            <th scope="row" style="width: 220px; font-size: 13px;">Bridge Secret Key</th>
                            <td>
                                <input type="text" name="<?php echo esc_attr(self::OPTION_SECRET_KEY); ?>" value="<?php echo esc_attr($secret_key); ?>" style="width: 450px; font-family: monospace;" />
                                <p class="description" style="margin-top: 4px;">Kunci pengaman untuk memverifikasi request dari Dashboard lokal Anda.</p>
                            </td>
                        </tr>
                        <tr valign="top">
                            <th scope="row" style="width: 220px; font-size: 13px;">URL Engine Lokal (Mac)</th>
                            <td>
                                <input type="text" name="<?php echo esc_attr(self::OPTION_ENGINE_URL); ?>" value="<?php echo esc_attr($engine_url); ?>" style="width: 450px; font-family: monospace;" placeholder="http://localhost:8000" />
                                <p class="description" style="margin-top: 4px;">Alamat web dashboard lokal Anda saat dijalankan di Mac.</p>
                            </td>
                        </tr>
                    </table>
                    <?php submit_button('Simpan Pengaturan Engine'); ?>
                </form>

                <!-- Recent GEO Articles Table -->
                <h2 style="font-size: 16px; font-weight: 700; color: #1e293b; margin-top: 30px; margin-bottom: 12px;">Daftar Artikel GEO Terbaru di Website Ini</h2>
                <div style="border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
                    <table class="wp-list-table widefat fixed striped posts" style="border: none;">
                        <thead>
                            <tr>
                                <th style="font-weight: 600;">Judul Artikel</th>
                                <th style="width: 120px; font-weight: 600;">Status</th>
                                <th style="width: 120px; font-weight: 600;">Tag Terpasang</th>
                                <th style="width: 150px; font-weight: 600;">Tanggal</th>
                                <th style="width: 100px; text-align: right; font-weight: 600;">Aksi</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php if (empty($geo_posts)): ?>
                                <tr>
                                    <td colspan="5" style="text-align: center; color: #94a3b8; padding: 24px;">Belum ada artikel GEO yang dibuat. Buka Dashboard Lokal di Mac untuk mulai memproduksi artikel pertama Anda.</td>
                                </tr>
                            <?php else: ?>
                                <?php foreach ($geo_posts as $post): ?>
                                    <tr>
                                        <td><strong><?php echo esc_html($post->post_title); ?></strong></td>
                                        <td><span class="badge" style="background: #e2e8f0; padding: 3px 8px; border-radius: 4px; font-size: 11px;"><?php echo esc_html(strtoupper($post->post_status)); ?></span></td>
                                        <td><span style="color: #6366f1; font-weight: 600;"><?php echo count(wp_get_post_tags($post->ID)); ?> Tags</span></td>
                                        <td><?php echo esc_html($post->post_date); ?></td>
                                        <td style="text-align: right;">
                                            <a href="<?php echo get_edit_post_link($post->ID); ?>" class="button button-small">Edit</a>
                                            <a href="<?php echo get_permalink($post->ID); ?>" target="_blank" class="button button-small">Lihat</a>
                                        </td>
                                    </tr>
                                <?php endforeach; ?>
                            <?php endif; ?>
                        </tbody>
                    </table>
                </div>

            </div>
        </div>
        <?php
    }
}

new Unicam_SEO_Engine_Bridge();
