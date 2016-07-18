/*!
 * gulp
 * $ npm install gulp-autoprefixer gulp-cssnano gulp-imagemin gulp-rename
 */

// Load plugins

var gulp = require('gulp'),
    autoprefixer = require('gulp-autoprefixer'),
    cssnano = require('gulp-cssnano'),
    imagemin = require('gulp-imagemin'),
    rename = require("gulp-rename"),
    path = require('path'),
    notify = require('gulp-notify');

// Images
// gulp.task('images', function() {
//   return gulp.src('restapi_app/static/restapi_app/img/**/*')
//     .pipe(imagemin({ optimizationLevel: 3, progressive: true, interlaced: true }))
//     .pipe(gulp.dest('dist/assets/img'))
//     .pipe(notify({ message: 'Images task complete' }));
// });

// Styles
// gulp.task('styles', function() {
//     // minify less/ css files and copy to css/filename/filename.min.css
//   return gulp.src('restapi_app/static/restapi_app/less/main.css')
//     .pipe(autoprefixer('last 2 version'))
//     .pipe(rename(function(file){
//         // join the base name (e.g., main) to the file path, effectively forcing gulp to create the folder if it doesn't
//         // exist already
//         file.dirname = path.join(file.dirname, file.basename)
//     }))
//     .pipe(rename({suffix: '.min'}))
//     .pipe(cssnano())
//     .pipe(gulp.dest('restapi_app/static/restapi_app/css/'))
//     // .pipe(notify({ message: 'Styles task complete' }));
// });


// Default task
// gulp.task('default', function(){
//     gulp.start('styles');
// });

// Watch
gulp.task('watch', function(){
    // watch the css files in the less directory (transpiler will update if less is altered)
    // minify and move to css/folder/
    gulp.watch(['../../**/static/**/less/**/*.css'], function(file){
    })
        .on("change", function(file){
            // console.log(file);

            var full_path= file.path;
            var static_path = full_path.split("less/")[0];
            var css_path = static_path+'css/';
            var less_path = static_path+'less/';
            var file_name = full_path.split("/").pop();
            var component_name = file_name.split(".css")[0];
            var new_dest = css_path+component_name+'/';

            var paths = {
                full_path: full_path,
                static_path: static_path,
                less_path: less_path,
                css_path: css_path,
                file_name: file_name,
                component_name: component_name,
                new_dest: new_dest
            };
            // console.log(paths);
            // console.log('----');
            return gulp.src(paths.full_path)
                .pipe(autoprefixer('last 2 version'))
                .pipe(rename({suffix: '.min'}))
                .pipe(cssnano())
                .pipe(gulp.dest(paths.new_dest))
                .pipe(notify({message: 'Gulp task complete: '+paths.new_dest}));
        })
});